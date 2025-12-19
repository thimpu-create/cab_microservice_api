# PassengerRegister


## Properties

Name | Type | Description | Notes
------------ | ------------- | ------------- | -------------
**fname** | **str** |  | 
**mname** | **str** |  | [optional] 
**lname** | **str** |  | 
**email** | **str** |  | 
**phone** | **str** |  | 
**password** | **str** |  | 

## Example

```python
from openapi_client.models.passenger_register import PassengerRegister

# TODO update the JSON string below
json = "{}"
# create an instance of PassengerRegister from a JSON string
passenger_register_instance = PassengerRegister.from_json(json)
# print the JSON string representation of the object
print(PassengerRegister.to_json())

# convert the object into a dict
passenger_register_dict = passenger_register_instance.to_dict()
# create an instance of PassengerRegister from a dict
passenger_register_from_dict = PassengerRegister.from_dict(passenger_register_dict)
```
[[Back to Model list]](../README.md#documentation-for-models) [[Back to API list]](../README.md#documentation-for-api-endpoints) [[Back to README]](../README.md)


