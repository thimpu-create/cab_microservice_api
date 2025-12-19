# VendorAdminRegister


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fname** | **str** |  | 
**mname** | **str** |  | [optional] 
**lname** | **str** |  | 
**email** | **str** |  | 
**phone** | **str** |  | 
**password** | **str** |  | 
**company_name** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.vendor_admin_register import VendorAdminRegister

# TODO update the JSON string below
json = "{}"
# create an instance of VendorAdminRegister from a JSON string
vendor_admin_register_instance = VendorAdminRegister.from_json(json)
# print the JSON string representation of the object
print(VendorAdminRegister.to_json())

# convert the object into a dict
vendor_admin_register_dict = vendor_admin_register_instance.to_dict()
# create an instance of VendorAdminRegister from a dict
vendor_admin_register_from_dict = VendorAdminRegister.from_dict(vendor_admin_register_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


