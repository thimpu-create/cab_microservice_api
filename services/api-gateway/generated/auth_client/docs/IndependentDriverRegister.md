# IndependentDriverRegister


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fname** | **str** |  | 
**mname** | **str** |  | [optional] 
**lname** | **str** |  | 
**email** | **str** |  | 
**phone** | **str** |  | 
**password** | **str** |  | 
**license_number** | **str** |  | [optional] 

## Example

```python
from openapi_client.models.independent_driver_register import IndependentDriverRegister

# TODO update the JSON string below
json = "{}"
# create an instance of IndependentDriverRegister from a JSON string
independent_driver_register_instance = IndependentDriverRegister.from_json(json)
# print the JSON string representation of the object
print(IndependentDriverRegister.to_json())

# convert the object into a dict
independent_driver_register_dict = independent_driver_register_instance.to_dict()
# create an instance of IndependentDriverRegister from a dict
independent_driver_register_from_dict = IndependentDriverRegister.from_dict(independent_driver_register_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


