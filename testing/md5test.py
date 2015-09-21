import subprocess

subprocess.check_call(["tar", "xfz",  "bridge_clone_inc.tar.gz"])
subprocess.call(["mv", "bridge_clone/md5", "md5"])
a = subprocess.Popen(("find", "bridge_clone", "-type", "f", "-print0"), stdout=subprocess.PIPE)
b = subprocess.Popen(("sort", "-z"), stdin=a.stdout, stdout=subprocess.PIPE)
c = subprocess.Popen(("xargs", "-r0", "md5sum"), stdin=b.stdout, stdout=subprocess.PIPE)
md5 = subprocess.check_output(("md5sum"), stdin=c.stdout)
with open("md5", "r") as f:
    md5orig = f.read()
print("Orig: %s", md5orig)
print("New: %s", md5)
print("Test: %s", md5==md5orig)
