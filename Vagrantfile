# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

$script = <<SCRIPT
apt-get update

apt-get -y install python-dev
apt-get -y install python-pip
apt-get -y install python-bottle
apt-get -y install sqlite3
apt-get -y install htop

ifconfig
SCRIPT

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
	config.vm.box = "ubuntu/trusty64"
	config.vm.hostname = "sharedb"
	#config.vm.network "public_network"
	config.vm.network "private_network", type: "dhcp"
	config.vm.synced_folder "./", "/vagrant"
	config.vm.provision "shell", inline: $script
end
