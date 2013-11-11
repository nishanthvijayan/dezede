#!/bin/sh

# Installe add-apt-repository.
apt-get install python-software-properties
# Ajout le dépôt PPA node.js.
add-apt-repository ppa:chris-lea/node.js
apt-get update

# Installe tous les paquets Ubuntu requis.
apt-get install nano postgresql python2.7 python-pip python-docutils python-dev redis-server libxml2 libxml2-dev libxslt1-dev rabbitmq-server nodejs

# Installe LESS CSS.
npm install -g less

# Installe le moteur de recherche elasticsearch.
wget https://download.elasticsearch.org/elasticsearch/elasticsearch/elasticsearch-0.90.6.deb
dpkg -i elasticsearch-*.deb
rm elasticsearch-*.deb

# Pour satisfaire la construction de python-imaging (alias PIL ou Pillow)
apt-get build-dep python-imaging

# Liens symboliques pour que PIL trouve ses dépendances.
# Sans cela, Django ne peut importer que des GIF et pas de JPEG, PNG, etc.
ln -s /usr/lib/`uname -i`-linux-gnu/libfreetype.so /usr/lib/
ln -s /usr/lib/`uname -i`-linux-gnu/libjpeg.so /usr/lib/
ln -s /usr/lib/`uname -i`-linux-gnu/libz.so /usr/lib/

# Installe tous les paquets python requis.
pip install -r requirements.txt
