# Collectd rabbitmq python plugin

This plugin requires Collectd python plugin and the python-requests package.
RabbitMQ needs to have the Management API plugin active.

Configuration example:

    <Plugin python>
             ModulePath "/usr/share/collectd/python"
             Import "rabbitmq"
             <Module rabbitmq>
                     User admin
                     Password admin
                     URL "http://localhost:15672/api/"
                     MonitorQueue "queue_name"
                     MonitorQueue "/somevhost" "anotherQueue"
             </Module>
    </Plugin>