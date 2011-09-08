#!/usr/bin/python

import sys
from debian import deb822

def find(f, seq):
  """Return first item in sequence where f(item) == True."""
  for item in seq:
    if f(item): 
      return item

def gen_package(binstr, version, release,arch):
	return map(lambda x: {'name':x.strip(), 'version':version, 'release':release, 'arch':arch}, binstr.split(','))

def flatten(listOfLists):
    return reduce(list.__add__, listOfLists)

def get_all_pkg_names(deps):
    dep_pkgs = map(lambda spkg: map(lambda pkg: pkg['name'], spkg['Binary']), deps)
    return flatten(dep_pkgs)
	
def process_dsc(fname):
	f = file(fname)
	pkg = deb822.Sources(f)
	version=pkg['Version'].split('-')[0]
	release=pkg['Version'].split('-')[1]
	return {'Source':pkg['Source'], 
                'Dsc':fname,
		'Version':version,
		'Release':release,
		'Binary':gen_package(pkg['Binary'],version,release,"i386"),
		'Build-Depends':map(lambda x: x.strip(), pkg['Build-Depends'].split(','))}

def get_binary_deb_name_from_package(pkg):
	return ("%s_%s-%s_%s.deb" % (pkg['name'], pkg['version'], pkg['release'], pkg['arch']))

def find_spkg_from_pkg_name(pkg_name, deps):
    return find(lambda spkg: pkg_name in map(lambda pkg: pkg['name'], spkg['Binary']), deps)

def find_pkg_from_pkg_name(pkg_name, deps):
    spkg = find_spkg_from_pkg_name(pkg_name, deps)
    if spkg:
        return find(lambda pkg: pkg['name']==pkg_name, spkg['Binary'])

def get_binary_deb_name_from_pkg_name(pkg_name,deps):
    package = find_pkg_from_pkg_name(pkg_name,deps)
    if package:
        return get_binary_deb_name_from_package(package)

    
def gen_deps(spkg, deps):
    pkg_names = get_all_pkg_names(deps)
    pkg_deps = filter(lambda name: name in pkg_names, spkg['Build-Depends'])
    for pkg in spkg['Binary']:
        debname=get_binary_deb_name_from_package(pkg)
        mydeps = map(lambda pkg_name: get_binary_deb_name_from_pkg_name(pkg_name,deps), pkg_deps)
#        deps = filter(lambda depname: depname <> None, deps)
        deps_str = ' '.join(mydeps)
        print "%s: %s %s" % (debname,spkg['Dsc'],deps_str)
        print "\t../build_deb.sh %s" % spkg['Dsc'] 

def gen_default_target(deps):
    pkg_names = get_all_pkg_names(deps)
    default=""
    for spkg in deps:
        for pkg in spkg['Binary']:
            default = "%s %s" % (default, get_binary_deb_name_from_package(pkg))

    print ".PHONY: default\ndefault : %s\n" % default
    print ".PHONY: fromcache\nfromcache : \n"

    for spkg in deps:
        for pkg in spkg['Binary']:
            print "\t$(shell ../fromcache.sh %s ) \n" % get_binary_deb_name_from_package(pkg)

    print ".PHONY: tocache\ntocache : \n"

    for spkg in deps:
        for pkg in spkg['Binary']:
            print "\t$(shell ../tocache.sh %s )\n" % get_binary_deb_name_from_package(pkg)






deps=map(process_dsc, sys.argv[1:])
gen_default_target(deps)
for spkg in deps:
	gen_deps(spkg, deps)

