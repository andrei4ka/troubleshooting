import re
import os
import commands
import json
import tempfile
import sys
import subprocess
import threading
import signal

class Alarm(Exception):
    pass

def alarm_handler(signum, frame):
    raise Alarm

class Platform():
  def __init__(self):
    if not os.system('gem list | grep ohai &>/dev/null') == 0 and not os.system('gem install ohai') == 0 and not os.system('gem install /var/www/nailgun/gems/gems/ohai*.gem') == 0:
      exit(1)
    self.raw_data = json.loads(commands.getoutput('ohai'))

  def pkglocalprovider(self):
    if self.getfamily() == "debian":
      return "dpkg -i"
    elif self.getfamily() == "redhat":
      return "rpm -ivh"
  
  def getpkgarch(self):
    if re.search('64', self.raw_data['kernel']['machine'], re.IGNORECASE):
      if self.getfamily() == "debian":
        return "amd64"
      elif self.getfamily() == "redhat":
        return "x86_64"
    elif re.search('i[0-9]86', self.raw_data['kernel']['machine'], re.IGNORECASE):
      if self.getfamily() == "debian":
        return "i686"
      elif self.getfamily() == "redhat":
        return "i386"

  def getpkgextension(self):
    if self.getfamily() == "debian":
      return "deb"
    elif self.getfamily() == "redhat":
      return "rpm" 

  def getfamily(self):
    if re.search('ubuntu', self.raw_data['platform'], re.IGNORECASE) or re.search('debian', self.raw_data['platform'], re.IGNORECASE) or re.search('debian', self.raw_data['platform_family'], re.IGNORECASE):
      return "debian"
    elif re.search('centos', self.raw_data['platform'], re.IGNORECASE) or re.search('redhat', self.raw_data['platform'], re.IGNORECASE) or re.search('rhel', self.raw_data['platform_family'], re.IGNORECASE):
      return "redhat"
    else:
      return "debian"

  def localinstall(self, pkg):
    install_cmd=self.pkglocalprovider() + ' ' + tmp_dir + pkg + '*' + self.getpkgarch() + '*.' + self.getpkgextension()
    if not os.system(install_cmd) == 0:
      print install_cmd, 'failed'


class Buildins():
  def __init__(self):
    self.platform = Platform()
    if os.path.isfile('/etc/fuel-uuid'):
      self.hostname = 'localhost'
    else:
      self.hostname = self.platform.raw_data['hostname']
    #print(self.hostname)

  def simplecmd(self, timeout, cmd):
    print 'going to run', cmd, timeout
    logfile = re.sub('[^a-zA-Z0-9]', '_', cmd)
    logfd = open(target_dir + logfile,'w')
    running = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=logfd, shell=True)
    signal.signal(signal.SIGALRM, alarm_handler)
    signal.alarm(int(timeout))
    try:
      errcode = running.wait()
      signal.alarm(0)
      logfd.write(str(cmd) + ' exit with ' + str(errcode))
      logfd.close()
    except Alarm:
     logfd.write(str(cmd) + ' exceed timeout ' + timeout)
     logfd.close()

  def localinstall(self, pkg):
    self.platform.localinstall(pkg)


class Nodes():
  def __init__(self):
    self.raw_data = json.loads(commands.getoutput('fuel --json node'))
    self.nodes = []
    os.system('cp ' + __file__ + ' ' + tmp_dir)
    for n in self.raw_data:
      self.nodes.append(n['fqdn'].split('.')[0])
      #distribute self and mine data
      os.system('scp -o "StrictHostKeyChecking no" -r ' + tmp_dir + ' ' + n['fqdn'] + ':' + re.sub('[^/]*/$','',tmp_dir))

  def runon_roles(self, cmd, role='ALL', async=False, timeout=120):
    pass

  def runon_node(self, node, cmd, async=False, timeout=120):
    if not node in self.nodes:
      return False
    else:
      print 'ssh -o "StrictHostKeyChecking no" ' + node + ' \'' + tmp_dir + __file__ + ' simplecmd ' + str(timeout) + ' "' + cmd + '"\''
      os.system('ssh -o "StrictHostKeyChecking no" ' + node + ' \'' + tmp_dir + __file__ + ' simplecmd ' + str(timeout) + ' "' + cmd + '"\'')

  def run_any2any(self, cmd, role='ALL', async=False, timeout=120):
    print lol

  def get_fromnode(self, node, target):
    pass

  def get_fromrole(self, role, target):
    pass


#me = Platform()
#me.localinstall("atop")

if len(sys.argv) == 1:
#i'm controller
  extract()
  pool = Nodes()
  pool.runon_node(node='node-9', cmd="ls /tmp/")
  #print pool.nodes
else:
#i'm target
  b = Buildins()
  print sys.argv
  #call = getattr(b,sys.argv[1])
  #import pdb; pdb.set_trace()
  #call(sys.argv[2:])
  if sys.argv[1] == 'simplecmd':
    b.simplecmd(sys.argv[2],sys.argv[3])
  if sys.argv[1] == 'localinstall':
    b.simplecmd(sys.argv[2],sys.argv[3])
