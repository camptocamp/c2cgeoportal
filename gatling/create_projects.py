from subprocess import check_call
from sys import argv

projects = ["ai", "az", "bb", "bn", "br", "bu", "cb", "cn", "co", "cr", "ct", "ec", "ee", "epa", "ep", "es", "ey", "gg", "gn", "gr", "gv", "jp", "lc", "lr", "ly", "md", "nstcm", "ol", "oo", "ou", "pe", "px", "pz", "tr", "ts", "tz", "vc", "vy"]



def main():

    '''check_call("git clone --depth 1 git@github.com:camptocamp/peitrequin_c2cgeoportal.git ref", shell=True)
    check_call("git submodule update --init", cwd="ref", shell=True)
    check_call("git submodule foreach git submodule update --init", cwd="ref", shell=True)
    check_call("rm -rf ref/.git", shell=True)
    check_call("mkdir buildout", shell=True)
    with open("ref/geoportal/run.cfg",'w') as f:
        f.write("""[buildout]
extends = buildout.cfg
eggs-directory = ../../buildout/eggs

[vars]
host = geocommunes.ch/ref
""")

    check_call("python bootstrap.py --version 1.5.2 --distribute --download-base http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/ --setup-source http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/distribute_setup.py", cwd="ref/geoportal", shell=True)
    check_call("./buildout/bin/buildout", cwd="ref/geoportal", shell=True)'''

    for n in range(int(argv[1])):
        check_call("cp -r ref {no}".format(no=n), shell=True)

        with open("{no}/geoportal/run.cfg".format(no=n),'w') as f:
            f.write("""[buildout]
extends = buildout.cfg
eggs-directory = ../../buildout/eggs
parts-directory = ../../buildout/parts
bin-directory = ../../buildout/bin

[vars]
apache-entry-point = /{no}/

schema = {project}
dataschema = data{project}
host = geocommunes.ch/{no}
appcfg = config_{project}.yaml
# used for mapfile and print template
commune = {project}""".format(no=n, project=projects[n%len(projects)]))

        check_call("python bootstrap.py --version 1.5.2 --distribute --download-base http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/ --setup-source http://pypi.camptocamp.net/distribute-0.6.22_fix-issue-227/distribute_setup.py", cwd="{no}/geoportal".format(no=n), shell=True)
        check_call("./buildout/bin/buildout -c run.cfg", cwd="{no}/geoportal".format(no=n), shell=True)

if __name__ == "__main__":
    main()
