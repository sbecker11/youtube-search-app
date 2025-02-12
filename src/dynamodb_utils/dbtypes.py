from typing import List, Dict, Any, Tuple
from boto3.resources.base import ServiceResource

DbSortDir = str # with values 'ASC', 'DESC'
DbAttr = str
DbItem = Dict[DbAttr, Any]
DbTable = ServiceResource
