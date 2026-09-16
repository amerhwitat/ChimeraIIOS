terraform {
  required_version = ">= 1.6.0"
  required_providers {
    openstack = {
      source  = "terraform-provider-openstack/openstack"
      version = ">= 1.54.0"
    }
  }
}

provider "openstack" {}

variable "image_id" { type = string }
variable "flavor_id" { type = string }
variable "network_id" { type = string }
variable "name" { type = string, default = "chimera-ii-os" }

resource "openstack_compute_instance_v2" "chimera" {
  name        = var.name
  image_id    = var.image_id
  flavor_id   = var.flavor_id
  network { uuid = var.network_id }
  stop_before_destroy = true
}

resource "openstack_blockstorage_volume_v3" "data" {
  count       = var.enable_volume ? 1 : 0
  name        = var.volume_name
  size        = var.volume_size_gb
  description = "Chimera II OS data volume"
}

resource "openstack_compute_volume_attach_v2" "data" {
  count       = var.enable_volume ? 1 : 0
  instance_id = openstack_compute_instance_v2.chimera.id
  volume_id   = openstack_blockstorage_volume_v3.data[0].id
}

resource "openstack_networking_floatingip_v2" "chimera" {
  count = var.enable_floating_ip ? 1 : 0
  pool  = var.floating_network_id
}

resource "openstack_compute_floatingip_associate_v2" "chimera" {
  count       = var.enable_floating_ip ? 1 : 0
  floating_ip = openstack_networking_floatingip_v2.chimera[0].address
  instance_id = openstack_compute_instance_v2.chimera.id
}

output "instance_id" { value = openstack_compute_instance_v2.chimera.id }
output "instance_name" { value = openstack_compute_instance_v2.chimera.name }
output "volume_id" { value = var.enable_volume ? openstack_blockstorage_volume_v3.data[0].id : null }
output "floating_ip" { value = var.enable_floating_ip ? openstack_networking_floatingip_v2.chimera[0].address : null }
