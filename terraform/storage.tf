resource "oci_objectstorage_bucket" "storage_bucket" { 
    compartment_id = var.compartment_ocid 
    name = var.bucket_name 
    namespace = data.oci_objectstorage_namespace.ns.namespace 
    storage_tier = "Standard" 
    access_type = "ObjectRead" 
}

resource "oci_core_volume" "block_volume" { 
    availability_domain = data.oci_identity_availability_domain.ad.name 
    compartment_id = var.compartment_ocid 
    display_name = "ZenVaultBV" 
    size_in_gbs = "50" 
}