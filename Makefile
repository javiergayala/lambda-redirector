.PHONY : pip-install copy-py-script dist scaffolding clean-build clean-dist clean-all
BASEDIR := $(shell pwd)
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
TOP := $(dir $(lastword $(MAKEFILE_LIST)))
BUILDDIR = ${ROOT_DIR}/build
DISTDIR = ${ROOT_DIR}/dist
LAMBDASCRIPT = lambda_redirector.py
REDIRECTIMPORTER = lambda_redirect_importer.py
REDIRECTUTILS = redirect_utils.py
LAMBDAZIPFILE = lambda_redirector.zip

dist: scaffolding copy-py-script
	cd ${BUILDDIR} && zip -r ${DISTDIR}/${LAMBDAZIPFILE} .
	@printf "\nLambda uploadable zip file created at ${DISTDIR}/${LAMBDAZIPFILE}\n"

copy-py-script:
	cp ${BASEDIR}/${LAMBDASCRIPT} ${BUILDDIR}
	cp ${BASEDIR}/${REDIRECTIMPORTER} ${BUILDDIR}
	cp ${BASEDIR}/${REDIRECTUTILS} ${BUILDDIR}

pip-install: scaffolding
	@python -m pip install -t ${BUILDDIR} -r requirements.txt

scaffolding:
	@mkdir -p ${BUILDDIR} ${DISTDIR}

clean-build:
	rm -rf ${BUILDDIR}

clean-dist:
	rm -rf ${DISTDIR}

clean-all: clean-build clean-dist scaffolding

clean: clean-all
