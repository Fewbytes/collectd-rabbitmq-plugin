# Collectd rabbitmq python plugin

# Configuration example:
#
#<Plugin python>
#         ModulePath "/usr/share/collectd/python"
#         Import "rabbitmq"
#
#         <Module rabbitmq>
#                 User admin
#                 Password admin
#                 URL "http://localhost:15672/api/"
#                 MonitorQueue "queue_name"
#				  MonitorQueue "/somevhost" "anotherQueue"
#         </Module>
# </Plugin>


import requests, urllib
import collectd

def urljoin(*parts):
	return "/".join(map(lambda s: s.rstrip("/"), parts))

def rabbit_api_call(url, user, password):
	collectd.debug("Polling on RabbitMQ admin API %s" % url)
	r = requests.get(url, auth=requests.auth.HTTPBasicAuth(user, password))
	if r.status_code == 200:
		return r.json()
	else:
		collectd.error("url %s returned status %d" % (url, r.status_code))
		return {}

def vhost_name(vhost):
	return "_default" if "/" else vhost.strip("/")

def dispatch_value(_type, type_instance, value):
	v = collectd.Values(plugin='python.rabbitmq')
	v.type = _type
	v.type_instance = type_instance
	v.dispatch(values=(value,))

def dispatch_complex_values(default_type, node, prefix=None):
	for metric_name, metric_value in node.iteritems():
		if type(metric_value) == int or type(metric_value) == float:
			dispatch_value(default_type, 
				".".join((prefix, metric_name)) if prefix else metric_name,
				metric_value)
		elif type(metric_value) == dict:
			dispatch_complex_values(default_type, metric_value, prefix=".".join((prefix, metric_name)))
		
def read_rabbitmq_metrics(config):
	for k, v in rabbit_api_call(urljoin(config['url'], 'overview'), config['user'], config['password']).iteritems():
		if k in ('object_totals', 'messages', 'queue_totals', 'message_stats'):
			dispatch_complex_values('gauge', v, 'general')
	for (vhost, queue) in config['monitored_queues']:
		dispatch_complex_values(
			'gauge',
			rabbit_api_call(
				urljoin(config['url'], 'queues', urllib.quote_plus(vhost), queue),
				config['user'],
				config['password']
			),
			"queues.%s-%s" % (vhost_name(vhost), queue)
		)


def plugin_config(collectd_config):
	plugin_config = {'url': 'http://localhost:55672/api/', 'monitored_queues': []}
	for child in collectd_config.children:
		if child.key == 'User':
			plugin_config['user'] = child.values[0]
		elif child.key == 'Password':
			plugin_config['password'] = child.values[0]
		elif child.key == 'URL':
			plugin_config['url'] = child.values[0]
		elif child.key == 'MonitorQueue':
			if len(child.values) == 2:
				vhost, queue = child.values[0:2]
			elif len(child.values) == 1:
				vhost, queue = "/", child.values[0]
			else:
				raise RuntimeError("MonitorQueue expects 1 or 2 params, no more.")
			plugin_config['monitored_queues'].append((vhost, queue))
		elif child.key.lower() == 'verbose':
			pass
		else:
			raise RuntimeError("Unknown config item %s" % child.key)
	
	collectd.register_read(read_rabbitmq_metrics, 10, plugin_config)


collectd.register_config(plugin_config)