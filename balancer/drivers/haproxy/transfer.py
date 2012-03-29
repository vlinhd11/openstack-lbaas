import logging

from fabric.api import env, sudo, get, put, run
from fabric.network import disconnect_all

from balancer.drivers.haproxy.Context import Context

logger = logging.getLogger(__name__)

class RemoteConfig(object):
    def __init__(self, context):
        env.user = context.login
        env.hosts = []
        env.hosts.append(context.ip)
        env.password = context.password
        env.host_string = context.ip
        self.localpath = context.localpath
        self.remotepath = context.remotepath
        self.localname = context.localname
        self.remotename = context.remotename
        
    def getConfig(self):
        get(self.remotepath + self.remotename, self.localpath + self.localname)
        disconnect_all()

    def putConfig(self):
        put(self.localpath+self.localname, '/tmp/'+self.remotename)
        sudo('mv /tmp/'+self.remotename + " "+ self.remotepath)
        disconnect_all()

    def validationConfig(self): 
        env.warn_only = True
        return (run('haproxy -c -f  %s/%s' % (self.remotepath,  self.remotename)) == 'Configuration file is valid')

class RemoteService(object):
    def __init__(self, context):
        env.user = context.login
        env.hosts = []
        env.hosts.append(context.ip)
        env.password = context.password
        env.host_string = context.ip
    
    def start(self):
        sudo('service haproxy start')
        disconnect_all()

    def stop(self):
        sudo('service haproxy stop')
        disconnect_all()
        
    def restart(self):
        sudo('service haproxy restart')
        disconnect_all()

class RemoteInterface(object):
    def __init__(self, context,  frontend):
        env.user = context.login
        env.hosts = []
        env.hosts.append(context.ip)
        env.password = context.password
        env.host_string = context.ip
        self.interface = context.interface
        self.IP = frontend.bind_address
        
    def changeIP(self, IP, netmask):
        sudo('ifconfig '+self.interface+ ' '+IP+' netmask '+netmask)
        disconnect_all()    
        
    def addIP(self):
        logger.debug('[HAPROXY] remote add ip %s to inteface %s' % (self.IP,  self.interface))        
        sudo('/sbin/ip addr add %s/32 dev %s'% (self.IP,  self.interface))
        disconnect_all()
        
    def delIP(self):
        logger.debug('[HAPROXY] remote delete ip %s from inteface %s' % (self.IP,  self.interface))
        sudo('/sbin/ip addr del %s/32 dev %s'% (self.IP,  self.interface))
        disconnect_all()