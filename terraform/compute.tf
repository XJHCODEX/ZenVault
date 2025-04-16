resource "oci_core_instance" "storage_server" { 
    compartment_id = var.compartment_ocid 
    availability_domain = data.oci_identity_availability_domain.ad.name
    display_name = "ZenVaultInstance" 
    shape = "VM.Standard.E2.1.Micro" 
    create_vnic_details { subnet_id = var.subnet_ocid } 
    source_details { 
        source_type = "image" 
        source_id = var.instance_image_ocid[var.region] 
    } 
    metadata = { 
        ssh_authorized_keys = var.ssh_public_key 
    } 
}