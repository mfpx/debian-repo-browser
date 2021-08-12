"""
---TODO---
config for tmp storage
bultiple mirror servers
better release directory structure
package manager-like cache updates
use **kwargs for multiple pkgs? or just *args
add cli support
"""

from ftplib import FTP
from pathlib import Path
import ftplib
import os
import os.path
import re
import gzip

ftp = FTP('ftp.us.debian.org') #debian mirror
ftp.login() #anon login
ftp.cwd('debian/dists') #initial distrib directory

print("---Distribution listing---")
total = 0
mlsd_errored = "False"

try:
    for line in ftp.mlsd():
        total += 1
        print(line)
    print("Total {} distributions available\n---End of listing---".format(total))
except ftplib.error_perm as err:
    print("This server does not support MLSD, it returned: {}\n---End of listing---\n".format(err))
    mlsd_errored = "True"

#remove tmp files
def localtmpclear():
    tmpdir = "tmp"
    for root, dirs, files in os.walk(tmpdir):
        for file in files:
            os.remove(os.path.join(root, file))

#TODO: path constructor to reduce code duplication
def constructpath(dir):
    pass

def pkgdl(pkgdir):
    ftp.pasv(true)
    ftp.cwd("/") #go back to ftp root
    print(ftp.size("debian/" + pkgdir))
    pkgname = pkgdir.split("/")
    print(pkgname)
    print("Downloading {}".format(pkgname[-1]))
    dlfile = open('dls/' + pkgname[-1], 'wb')
    ftp.retrbinary('RETR /debian/' + pkgdir, dlfile.write)

def pkgsearch():
    pkg = input("Search query: ")
    pkg = "Package: " + pkg
    pkgfound = 0
    singlepkg = 0
    relfile = open("tmp/Release", "r")
    for line in relfile:
        if pkg in line:
            print("\n---Results---")
            pkgfound = 1
        if pkgfound == 1:
            if line in ['\n', '\r\n']:
                pkgfound = 0
            else:
                print(line.rstrip('\r\n'))
                if "Filename:" in line:
                    singlepkg = 1
                    filename = line.replace("Filename: ","")
                    pkgdl(filename)
    if pkgfound == 0:
        print("No packages for \"{}\" found\nTry again...".format(pkg))
        pkgsearch()

def pkglisting(retries = 0):
    pkgcache = Path("tmp/Release")
    if pkgcache.is_file():
        print("Local package cache found, continuing...")
        pkgsearch()
    else:
        if retries <= 3:
            print("Downloading package cache...")
            with open('tmp/Packages.gz', 'wb') as fp:
                ftp.retrbinary('RETR Packages.gz', fp.write)
            pkgpath = Path("tmp/Packages.gz") #TODO: feature to allow users to save to their os tmp dir
            relpath = Path("tmp/Release")
            if pkgpath.is_file():
                print("Download OK, continuing...")
                fp = open("tmp/Release", "wb")
                with gzip.open('tmp/Packages.gz', 'rb') as out:
                    bindata = out.read()
                fp.write(bindata)
                fp.close()
            if relpath.is_file():
                print("Extract OK, continuing...")
                pkgsearch()
            else:
                print("[{}/3]: Download failed, retrying...".format(retries))
                retries += 1
                pkglisting(retries)
        else:
            print("Try limit exceeded, giving up...")
            os._exit(1)


def archsel():
    #allows the user to select a specific architecture
    print("---Architecture listing---")
    for line in ftp.nlst():
        if "binary" in line:
            print(line.replace('binary-',''))
    print("---End of listing---")
    arch = input("Select your architecture: ")
    try:
        ftp.cwd("binary-" + arch)
        pkglisting()
    except ftplib.error_perm as err:
        print("No such architecture found, server returned: {}\nTry again...".format(err))
        archsel()

def reposel():
    # allows the user to select a specific repository
    print("Repos available: main, contrib and non-free")
    repo = input("Select your repository: ")
    try:
        ftp.cwd(repo)
        archsel()
    except ftplib.error_perm as err:
        print("No such repository found, server returned: {}\nTry again...".format(err))
        reposel()

def distsel():
    # allows the user to select a specific distribution
    dist = input("Select your distribution: ")
    try:
        ftp.cwd(dist)
        reposel()
    except ftplib.error_perm as err:
        print("No such distribution found, server returned: {}\nTry again...".format(err))
        distsel()

if mlsd_errored == "True":
    print("Attempting non-MLSD directory listing...\n")
    print("---Distribution listing---")
    try:
        for line in ftp.nlst():
            print(line)
            total += 1
        print("---End of listing---")
        print("\nA total of {} items listed\nNOTE: Some of these items MIGHT NOT be distributions".format(total))
        distsel()
    except:
        print("Attempted 2 supported methods, they didn't work, giving up...")
        ftp.quit()
        os._exit(1)

ftp.quit()
