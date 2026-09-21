from chimera_sdk import sdk_version,target_triple,host_info
assert sdk_version()=="1.0.0"
assert target_triple().startswith("chimera-")
assert "python" in host_info()
print("Chimera SDK Python smoke: OK")
