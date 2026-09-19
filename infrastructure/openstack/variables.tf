variable "enable_volume" {
  type    = bool
  default = false
}

variable "volume_size_gb" {
  type    = number
  default = 20
}

variable "volume_name" {
  type    = string
  default = "chimera-ii-os-data"
}

variable "enable_floating_ip" {
  type    = bool
  default = false
}

variable "floating_network_id" {
  type    = string
  default = null
}
