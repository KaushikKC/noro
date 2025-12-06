"""
NeoFS Integration Client
Based on: https://github.com/XSpoonAi/spoon-core/blob/08038bff7cf74440a1253bb13948a92106d758d2/examples/neofs-agent-demo.py#L260

Python backend integration with NeoFS using spoon_ai.tools.neofs_tools
Following the reference implementation pattern
"""
import asyncio
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load .env file first
load_dotenv(override=True)

# Import NeoFS tools from spoon_ai
try:
    from spoon_ai.tools.neofs_tools import (
        CreateBearerTokenTool,
        CreateContainerTool,
        UploadObjectTool,
        SetContainerEaclTool,
        GetContainerEaclTool,
        ListContainersTool,
        GetContainerInfoTool,
        DeleteContainerTool,
        GetNetworkInfoTool,
        DownloadObjectByIdTool,
        GetObjectHeaderByIdTool,
        DownloadObjectByAttributeTool,
        GetObjectHeaderByAttributeTool,
        DeleteObjectTool,
        SearchObjectsTool,
        GetBalanceTool,
    )
    NEOFS_TOOLS_AVAILABLE = True
except ImportError:
    NEOFS_TOOLS_AVAILABLE = False
    print("Warning: spoon_ai.tools.neofs_tools not available. Install spoon-ai-sdk.")


class NeoFSClient:
    """
    Client for interacting with NeoFS network
    Uses spoon_ai.tools.neofs_tools following reference implementation
    """
    
    def __init__(
        self,
        gateway_url: Optional[str] = None,
        network: str = "testnet"
    ):
        """
        Initialize NeoFS client
        
        Args:
            gateway_url: NeoFS HTTP gateway endpoint (e.g., https://rest.fs.neo.org)
            network: Network type ('mainnet' or 'testnet')
        """
        if not NEOFS_TOOLS_AVAILABLE:
            raise ImportError(
                "spoon_ai.tools.neofs_tools not available. "
                "Please install spoon-ai-sdk: pip install spoon-ai-sdk"
            )
        
        self.network = network
        self.gateway_url = gateway_url or os.getenv(
            "NEOFS_ENDPOINT",
            "https://rest.fs.neo.org"
        )
        
        # Initialize tools
        self.create_bearer_token_tool = CreateBearerTokenTool()
        self.create_container_tool = CreateContainerTool()
        self.upload_object_tool = UploadObjectTool()
        self.list_containers_tool = ListContainersTool()
        self.get_container_info_tool = GetContainerInfoTool()
        self.delete_container_tool = DeleteContainerTool()
        self.download_object_by_id_tool = DownloadObjectByIdTool()
        self.download_object_by_attribute_tool = DownloadObjectByAttributeTool()
        self.get_object_header_by_id_tool = GetObjectHeaderByIdTool()
        self.get_object_header_by_attribute_tool = GetObjectHeaderByAttributeTool()
        self.delete_object_tool = DeleteObjectTool()
        self.search_objects_tool = SearchObjectsTool()
        self.get_network_info_tool = GetNetworkInfoTool()
        self.get_balance_tool = GetBalanceTool()
        self.set_container_eacl_tool = SetContainerEaclTool()
        self.get_container_eacl_tool = GetContainerEaclTool()
    
    async def create_bearer_token(
        self,
        token_type: str,
        verb: Optional[str] = None,
        operation: Optional[str] = None,
        container_id: Optional[str] = None,
        lifetime: int = 3600
    ) -> Dict[str, Any]:
        """
        Create a bearer token for NeoFS operations
        
        Args:
            token_type: "container" or "object"
            verb: For container tokens: "PUT", "DELETE", "SETEACL"
            operation: For object tokens: "PUT", "GET", "DELETE"
            container_id: Container ID (required for DELETE and SETEACL)
            lifetime: Token lifetime in seconds (default: 3600)
            
        Returns:
            Dict containing bearer token information
        """
        params = {
            "token_type": token_type,
            "lifetime": lifetime
        }
        
        if token_type == "container":
            if verb:
                params["verb"] = verb
            if container_id:
                params["container_id"] = container_id
        elif token_type == "object":
            if operation:
                params["operation"] = operation
            if container_id:
                params["container_id"] = container_id
        
        result = await self.create_bearer_token_tool.execute(**params)
        return result.output if hasattr(result, 'output') else result
    
    async def create_container(
        self,
        name: str,
        bearer_token: Optional[str] = None,
        basic_acl: str = "public-read-write",
        placement_policy: str = "REP 1",
        attributes: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new NeoFS container
        
        Args:
            name: Container name
            bearer_token: Bearer token for container creation (required)
            basic_acl: Basic ACL setting ("public-read-write" or "eacl-public-read-write")
            placement_policy: Placement policy (default: "REP 1")
            attributes: Optional container attributes
            
        Returns:
            Dict containing container information including container_id
        """
        # Create bearer token if not provided
        if not bearer_token:
            token_result = await self.create_bearer_token(
                token_type="container",
                verb="PUT"
            )
            # Extract token from result
            if isinstance(token_result, dict):
                bearer_token = token_result.get("bearer_token") or token_result.get("token")
            elif isinstance(token_result, str):
                bearer_token = token_result
        
        params = {
            "name": name,
            "bearer_token": bearer_token,
            "basic_acl": basic_acl,
            "placement_policy": placement_policy
        }
        
        if attributes:
            params["attributes_json"] = json.dumps(attributes)
        
        result = await self.create_container_tool.execute(**params)
        return result.output if hasattr(result, 'output') else result
    
    async def list_containers(self) -> List[Dict[str, Any]]:
        """List all containers for the authenticated wallet"""
        result = await self.list_containers_tool.execute()
        output = result.output if hasattr(result, 'output') else result
        # Parse output if it's a string
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except:
                pass
        return output if isinstance(output, list) else []
    
    async def get_container_info(self, container_id: str) -> Dict[str, Any]:
        """Get detailed information about a container"""
        result = await self.get_container_info_tool.execute(container_id=container_id)
        output = result.output if hasattr(result, 'output') else result
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except:
                pass
        return output if isinstance(output, dict) else {}
    
    async def delete_container(self, container_id: str) -> bool:
        """Delete a container"""
        # Create DELETE bearer token
        token_result = await self.create_bearer_token(
            token_type="container",
            verb="DELETE",
            container_id=container_id
        )
        bearer_token = token_result.get("bearer_token") or token_result.get("token") if isinstance(token_result, dict) else token_result
        
        result = await self.delete_container_tool.execute(
            container_id=container_id,
            bearer_token=bearer_token
        )
        return result.output if hasattr(result, 'output') else result
    
    async def upload_object(
        self,
        container_id: str,
        file_path: Optional[str] = None,
        content: Optional[str] = None,
        attributes_json: Optional[str] = None,
        bearer_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload an object to NeoFS
        
        Args:
            container_id: Container ID to upload to
            file_path: Path to file to upload (recommended for large files)
            content: Base64-encoded content (for small files)
            attributes_json: JSON string of attributes (e.g., '{"FileName": "test.txt"}')
            bearer_token: Bearer token (required for eACL containers, not needed for PUBLIC)
            
        Returns:
            Dict containing object_id and other metadata
        """
        params = {
            "container_id": container_id
        }
        
        if file_path:
            params["file_path"] = file_path
        elif content:
            params["content"] = content
        else:
            raise ValueError("Either file_path or content must be provided")
        
        if attributes_json:
            params["attributes_json"] = attributes_json
        
        if bearer_token:
            params["bearer_token"] = bearer_token
        
        result = await self.upload_object_tool.execute(**params)
        output = result.output if hasattr(result, 'output') else result
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except:
                pass
        return output
    
    async def download_object_by_id(
        self,
        container_id: str,
        object_id: str,
        save_path: Optional[str] = None,
        bearer_token: Optional[str] = None
    ) -> bytes:
        """
        Download an object by ID
        
        Args:
            container_id: Container ID
            object_id: Object ID to download
            save_path: Optional path to save the file
            bearer_token: Bearer token (required for eACL containers)
            
        Returns:
            Binary data of the object
        """
        params = {
            "container_id": container_id,
            "object_id": object_id
        }
        
        if save_path:
            params["save_path"] = save_path
        
        if bearer_token:
            params["bearer_token"] = bearer_token
        
        result = await self.download_object_by_id_tool.execute(**params)
        output = result.output if hasattr(result, 'output') else result
        return output
    
    async def download_object_by_attribute(
        self,
        container_id: str,
        attr_key: str,
        attr_val: str,
        save_path: Optional[str] = None,
        bearer_token: Optional[str] = None
    ) -> bytes:
        """
        Download an object by attribute
        
        Args:
            container_id: Container ID
            attr_key: Attribute key (e.g., "FileName")
            attr_val: Attribute value (e.g., "test.txt")
            save_path: Optional path to save the file
            bearer_token: Bearer token (required for eACL containers)
            
        Returns:
            Binary data of the object
        """
        params = {
            "container_id": container_id,
            "attr_key": attr_key,
            "attr_val": attr_val
        }
        
        if save_path:
            params["save_path"] = save_path
        
        if bearer_token:
            params["bearer_token"] = bearer_token
        
        result = await self.download_object_by_attribute_tool.execute(**params)
        output = result.output if hasattr(result, 'output') else result
        return output
    
    async def search_objects(
        self,
        container_id: str,
        filters: Optional[List[Dict[str, str]]] = None,
        bearer_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for objects in a container
        
        Args:
            container_id: Container ID
            filters: List of filter dicts [{"key": "FileName", "value": "test.txt"}]
            bearer_token: Bearer token (required for eACL containers)
            
        Returns:
            List of matching objects
        """
        params = {
            "container_id": container_id
        }
        
        if filters:
            params["filters"] = filters
        
        if bearer_token:
            params["bearer_token"] = bearer_token
        
        result = await self.search_objects_tool.execute(**params)
        output = result.output if hasattr(result, 'output') else result
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except:
                pass
        return output if isinstance(output, list) else []
    
    async def delete_object(
        self,
        container_id: str,
        object_id: str,
        bearer_token: Optional[str] = None
    ) -> bool:
        """
        Delete an object from NeoFS
        
        Args:
            container_id: Container ID
            object_id: Object ID to delete
            bearer_token: Bearer token (usually not needed for delete)
            
        Returns:
            True if successful
        """
        params = {
            "container_id": container_id,
            "object_id": object_id
        }
        
        if bearer_token:
            params["bearer_token"] = bearer_token
        
        result = await self.delete_object_tool.execute(**params)
        output = result.output if hasattr(result, 'output') else result
        return output
    
    async def get_network_info(self) -> Dict[str, Any]:
        """Get NeoFS network information"""
        result = await self.get_network_info_tool.execute()
        output = result.output if hasattr(result, 'output') else result
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except:
                pass
        return output if isinstance(output, dict) else {}
    
    async def get_balance(self) -> Dict[str, Any]:
        """Get NeoFS account balance"""
        result = await self.get_balance_tool.execute()
        output = result.output if hasattr(result, 'output') else result
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except:
                pass
        return output if isinstance(output, dict) else {}
    
    # Helper methods for market data
    async def upload_market_data(
        self,
        container_id: str,
        market_id: str,
        data: Dict[str, Any],
        bearer_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload market data to NeoFS
        
        Args:
            container_id: Container ID
            market_id: Market identifier
            data: Market data dictionary
            bearer_token: Bearer token (if eACL container)
            
        Returns:
            Dict containing object_id and metadata
        """
        # Convert data to JSON string
        json_content = json.dumps(data, indent=2)
        json_base64 = json_content.encode('utf-8')
        import base64
        content_base64 = base64.b64encode(json_base64).decode('utf-8')
        
        attributes = {
            "market_id": market_id,
            "timestamp": str(int(datetime.now().timestamp())),
            "content_type": "application/json",
            "FileName": f"market_{market_id}_{datetime.now().isoformat()}.json"
        }
        
        return await self.upload_object(
            container_id=container_id,
            content=content_base64,
            attributes_json=json.dumps(attributes),
            bearer_token=bearer_token
        )
    
    async def upload_market_data(
        self,
        container_id: str,
        market_id: str,
        market_data: Dict[str, Any],
        bearer_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload market data to NeoFS
        
        Args:
            container_id: Container ID
            market_id: Market identifier
            market_data: Market data dictionary (question, description, category, etc.)
            bearer_token: Bearer token (if eACL container)
            
        Returns:
            Dict containing object_id and metadata
        """
        attributes = {
            "market_id": market_id,
            "type": "market_data",
            "timestamp": str(int(datetime.now().timestamp())),
            "content_type": "application/json",
            "FileName": f"market_{market_id}.json"
        }
        
        # Convert market data to JSON and base64 encode
        json_content = json.dumps(market_data, indent=2)
        import base64
        content_base64 = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
        
        return await self.upload_object(
            container_id=container_id,
            content=content_base64,
            attributes_json=json.dumps(attributes),
            bearer_token=bearer_token
        )
    
    async def get_market_data(
        self,
        container_id: str,
        market_id: str,
        bearer_token: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get market data from NeoFS by market_id
        
        Args:
            container_id: Container ID
            market_id: Market identifier
            bearer_token: Bearer token (if eACL container)
            
        Returns:
            Market data dictionary or None if not found
        """
        try:
            # Search for objects with market_id attribute
            filters = [{"key": "market_id", "value": market_id}, {"key": "type", "value": "market_data"}]
            objects = await self.search_objects(
                container_id=container_id,
                filters=filters,
                bearer_token=bearer_token
            )
            
            if not objects or len(objects) == 0:
                return None
            
            # Get the most recent market data (first result)
            object_info = objects[0]
            object_id = object_info.get("object_id") or object_info.get("id")
            
            if not object_id:
                return None
            
            # Download the object
            result_bytes = await self.download_object_by_id(
                container_id=container_id,
                object_id=object_id,
                bearer_token=bearer_token
            )
            
            # Parse JSON from bytes
            if isinstance(result_bytes, bytes):
                json_str = result_bytes.decode('utf-8')
            else:
                json_str = str(result_bytes)
            
            return json.loads(json_str)
        except Exception as e:
            print(f"Error getting market data from NeoFS: {e}")
            return None
    
    async def list_all_markets(
        self,
        container_id: str,
        bearer_token: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List all market data from NeoFS
        
        Args:
            container_id: Container ID
            bearer_token: Bearer token (if eACL container)
            
        Returns:
            List of market data dictionaries
        """
        try:
            # Search for all objects with type="market_data"
            filters = [{"key": "type", "value": "market_data"}]
            objects = await self.search_objects(
                container_id=container_id,
                filters=filters,
                bearer_token=bearer_token
            )
            
            if not objects:
                return []
            
            markets = []
            for obj_info in objects:
                object_id = obj_info.get("object_id") or obj_info.get("id")
                if not object_id:
                    continue
                
                try:
                    # Download the object
                    result_bytes = await self.download_object_by_id(
                        container_id=container_id,
                        object_id=object_id,
                        bearer_token=bearer_token
                    )
                    
                    # Parse JSON
                    if isinstance(result_bytes, bytes):
                        json_str = result_bytes.decode('utf-8')
                    else:
                        json_str = str(result_bytes)
                    
                    market_data = json.loads(json_str)
                    markets.append(market_data)
                except Exception as e:
                    print(f"Error parsing market data for object {object_id}: {e}")
                    continue
            
            return markets
        except Exception as e:
            print(f"Error listing markets from NeoFS: {e}")
            return []
    
    async def upload_agent_analysis(
        self,
        container_id: str,
        market_id: str,
        analysis: Dict[str, Any],
        bearer_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload agent analysis results to NeoFS
        
        Args:
            container_id: Container ID
            market_id: Market identifier
            analysis: Analysis data dictionary
            bearer_token: Bearer token (if eACL container)
            
        Returns:
            Dict containing object_id and metadata
        """
        attributes = {
            "market_id": market_id,
            "type": "agent_analysis",
            "timestamp": str(int(datetime.now().timestamp())),
            "content_type": "application/json",
            "FileName": f"analysis_{market_id}_{datetime.now().isoformat()}.json"
        }
        
        # Convert analysis to JSON and base64 encode
        json_content = json.dumps(analysis, indent=2)
        import base64
        content_base64 = base64.b64encode(json_content.encode('utf-8')).decode('utf-8')
        
        return await self.upload_object(
            container_id=container_id,
            content=content_base64,
            attributes_json=json.dumps(attributes),
            bearer_token=bearer_token
        )
