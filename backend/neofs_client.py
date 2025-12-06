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
        
        # Set NeoFS configuration environment variables for tools
        # The spoon_ai.tools.neofs_tools use NeoFSClient which expects:
        # NEOFS_BASE_URL, NEOFS_OWNER_ADDRESS, NEOFS_PRIVATE_KEY_WIF
        # (matching the client example you provided)
        base_url = self.gateway_url
        
        # Set NEOFS_BASE_URL if not already set
        if not os.getenv("NEOFS_BASE_URL"):
            os.environ["NEOFS_BASE_URL"] = base_url
        
        # Get owner_address and private_key_wif from environment
        # These must be set in .env file: NEOFS_OWNER_ADDRESS and NEOFS_PRIVATE_KEY_WIF
        owner_address = os.getenv("NEOFS_OWNER_ADDRESS", "")
        private_key_wif = os.getenv("NEOFS_PRIVATE_KEY_WIF", "")
        
        # CRITICAL: Set these in environment for the tools to use
        # The tools read from environment variables, so we must set them here
        if owner_address:
            os.environ["NEOFS_OWNER_ADDRESS"] = owner_address
        if private_key_wif:
            os.environ["NEOFS_PRIVATE_KEY_WIF"] = private_key_wif
        
        # Debug: Check if credentials are set
        print(f"🔍 [NEOFS] Configuration check:")
        print(f"   NEOFS_BASE_URL: {base_url}")
        print(f"   NEOFS_OWNER_ADDRESS: {'SET' if owner_address else 'NOT SET'} ({len(owner_address)} chars)")
        if owner_address:
            print(f"   Owner address preview: {owner_address[:20]}...")
        print(f"   NEOFS_PRIVATE_KEY_WIF: {'SET' if private_key_wif else 'NOT SET'} ({len(private_key_wif)} chars)")
        
        if not owner_address or not private_key_wif:
            print(f"⚠️ [NEOFS] Missing credentials! Set NEOFS_OWNER_ADDRESS and NEOFS_PRIVATE_KEY_WIF in .env")
            print(f"   Operations will fail until credentials are set.")
            print(f"   The ASCII error is likely because owner_address is empty or invalid.")
        
        # Store for reference
        self.owner_address = owner_address
        self.private_key_wif = private_key_wif
        self.base_url = base_url
        
        # Validate that owner_address and private_key_wif are ASCII-only
        if owner_address:
            try:
                owner_address.encode('ascii')
                print(f"✅ [NEOFS] Owner address is ASCII-valid")
            except UnicodeEncodeError:
                raise ValueError(f"NEOFS_OWNER_ADDRESS contains non-ASCII characters: {owner_address[:20]}...")
        else:
            print(f"❌ [NEOFS] Owner address is EMPTY - this will cause ASCII errors!")
        
        if private_key_wif:
            try:
                private_key_wif.encode('ascii')
                print(f"✅ [NEOFS] Private key is ASCII-valid")
            except UnicodeEncodeError:
                raise ValueError(f"NEOFS_PRIVATE_KEY_WIF contains non-ASCII characters")
        else:
            print(f"❌ [NEOFS] Private key is EMPTY - this will cause ASCII errors!")
        
        # Note: The tools will read these from environment variables automatically
        # No need to pass them explicitly to tool constructors
        
        # Initialize tools (they will read from environment variables)
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
        try:
            print(f"🔑 [NEOFS] Creating bearer token: type={token_type}, verb={verb}, operation={operation}")
            
            # The tool signature shows: execute(token_type, verb='PUT', operation='PUT', container_id='', lifetime=100)
            # For container tokens with verb="PUT" (creating container), container_id should be empty string
            # The tool needs all parameters explicitly set
            params = {
                "token_type": token_type,
                "lifetime": lifetime
            }
            
            # For container tokens
            if token_type == "container":
                # Container tokens use 'verb' parameter
                params["verb"] = verb or "PUT"  # Default to PUT if not specified
                params["operation"] = ""  # Empty for container tokens
                # For PUT (create), container_id should be empty string
                # For DELETE/SETEACL, container_id is required
                if params["verb"] in ["DELETE", "SETEACL"]:
                    if not container_id:
                        raise ValueError(f"container_id is required for {params['verb']} operation")
                    params["container_id"] = container_id
                else:
                    params["container_id"] = ""  # Empty for PUT (create new container)
            
            # For object tokens
            elif token_type == "object":
                # Object tokens use 'operation' parameter
                params["operation"] = operation or "PUT"  # Default to PUT if not specified
                params["verb"] = ""  # Empty for object tokens
                params["container_id"] = container_id or ""  # Optional for object tokens
            
            print(f"🔑 [NEOFS] Bearer token params: {params}")
            print(f"🔑 [NEOFS] Owner address available: {self.owner_address[:20] if self.owner_address else 'NOT SET'}...")
            print(f"🔑 [NEOFS] Private key available: {'SET' if self.private_key_wif else 'NOT SET'}")
            
            # CRITICAL: Verify environment variables are set before calling tool
            # The tool reads owner_address from NEOFS_OWNER_ADDRESS env var
            env_owner = os.getenv("NEOFS_OWNER_ADDRESS", "")
            env_key = os.getenv("NEOFS_PRIVATE_KEY_WIF", "")
            print(f"🔑 [NEOFS] Environment check - Owner: {'SET' if env_owner else 'NOT SET'}, Key: {'SET' if env_key else 'NOT SET'}")
            
            if not env_owner or not env_key:
                error_msg = (
                    f"NeoFS credentials not set in environment! "
                    f"Owner: {'SET' if env_owner else 'MISSING'}, "
                    f"Key: {'SET' if env_key else 'MISSING'}. "
                    f"Set NEOFS_OWNER_ADDRESS and NEOFS_PRIVATE_KEY_WIF in .env file."
                )
                print(f"❌ [NEOFS] {error_msg}")
                raise ValueError(error_msg)
            
            # Verify owner_address is ASCII before tool call
            try:
                env_owner.encode('ascii')
            except UnicodeEncodeError:
                raise ValueError(f"NEOFS_OWNER_ADDRESS contains non-ASCII characters: {env_owner[:20]}...")
            
            result = await self.create_bearer_token_tool.execute(**params)
            output = result.output if hasattr(result, 'output') else result
            
            # Debug: Check what we got back (but strip emojis for display)
            output_str = str(output)
            # Remove emojis for logging
            import re
            output_clean = re.sub(r'[^\x00-\x7F]+', '[NON-ASCII]', output_str)
            print(f"🔑 [NEOFS] Tool result type: {type(output)}")
            print(f"🔑 [NEOFS] Tool result (first 200 chars, emojis removed): {output_clean[:200]}")
            
            # The tool might return a string with the token, or a dict
            # If it's a string, it might be JSON or just the token
            if isinstance(output, str):
                # Check if it contains emojis (error message)
                if "❌" in output or "✅" in output or "⚠️" in output:
                    # Try to extract the actual token from the message
                    # Look for base64-like strings (long alphanumeric strings)
                    import re
                    base64_pattern = r'[A-Za-z0-9+/=]{50,}'  # Base64 tokens are usually long
                    matches = re.findall(base64_pattern, output)
                    if matches:
                        # Use the longest match (likely the token)
                        token = max(matches, key=len)
                        print(f"🔑 [NEOFS] Extracted token from message (length: {len(token)})")
                        return {"bearer_token": token}
                    else:
                        print(f"❌ [NEOFS] Tool returned error message with no token: {output[:200]}")
                        raise ValueError(f"Bearer token creation failed: {output}")
                
                # Check if it's JSON
                try:
                    import json
                    parsed = json.loads(output)
                    if isinstance(parsed, dict):
                        output = parsed
                        print(f"🔑 [NEOFS] Parsed JSON result: {list(parsed.keys())}")
                except:
                    # Not JSON, assume it's the token itself
                    print(f"🔑 [NEOFS] Tool returned string token (length: {len(output)})")
            
            # Extract bearer token from dict if needed
            if isinstance(output, dict):
                bearer_token_value = output.get("bearer_token") or output.get("token") or output.get("value")
                if bearer_token_value:
                    print(f"🔑 [NEOFS] Extracted bearer token from dict (length: {len(bearer_token_value)})")
                    return {"bearer_token": bearer_token_value, **output}
                else:
                    print(f"⚠️ [NEOFS] Dict result but no bearer_token key: {list(output.keys())}")
            
            print(f"🔑 [NEOFS] Bearer token created successfully")
            return output
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [NEOFS] Error creating bearer token: {error_msg}")
            if "ASCII" in error_msg or "ascii" in error_msg.lower():
                print(f"   ⚠️  ASCII error in bearer token creation!")
                print(f"   This suggests NEOFS_OWNER_ADDRESS or NEOFS_PRIVATE_KEY_WIF has encoding issues")
                print(f"   Owner address: {self.owner_address[:20] if self.owner_address else 'NOT SET'}...")
                print(f"   Private key set: {'YES' if self.private_key_wif else 'NO'}")
                print(f"   Environment Owner: {os.getenv('NEOFS_OWNER_ADDRESS', 'NOT SET')[:20]}...")
                print(f"   Environment Key: {'SET' if os.getenv('NEOFS_PRIVATE_KEY_WIF') else 'NOT SET'}")
            import traceback
            traceback.print_exc()
            raise
    
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
            print(f"🔑 [NEOFS] Creating container bearer token...")
            try:
                token_result = await self.create_bearer_token(
                    token_type="container",
                    verb="PUT"
                )
                # Extract token from result
                print(f"🔑 [NEOFS] Token result type: {type(token_result)}")
                print(f"🔑 [NEOFS] Token result preview: {str(token_result)[:200]}")
                
                if isinstance(token_result, dict):
                    bearer_token = token_result.get("bearer_token") or token_result.get("token") or token_result.get("value")
                    print(f"🔑 [NEOFS] Extracted from dict: {list(token_result.keys())}")
                elif isinstance(token_result, str):
                    # Check if it contains emojis (error message with formatted output)
                    if "❌" in token_result or "✅" in token_result or "⚠️" in token_result:
                        # Try to extract the actual token from the message
                        # Look for base64-like strings (long alphanumeric strings)
                        import re
                        base64_pattern = r'[A-Za-z0-9+/=]{50,}'  # Base64 tokens are usually long
                        matches = re.findall(base64_pattern, token_result)
                        if matches:
                            # Use the longest match (likely the token)
                            bearer_token = max(matches, key=len)
                            print(f"🔑 [NEOFS] Extracted token from formatted message (length: {len(bearer_token)})")
                        else:
                            print(f"❌ [NEOFS] Tool returned error message with no extractable token!")
                            raise ValueError(f"Bearer token creation failed: {token_result[:200]}")
                    # Check if it's JSON string
                    elif token_result.strip().startswith('{'):
                        try:
                            import json
                            parsed = json.loads(token_result)
                            if isinstance(parsed, dict):
                                bearer_token = parsed.get("bearer_token") or parsed.get("token") or parsed.get("value")
                                print(f"🔑 [NEOFS] Parsed JSON string, extracted token")
                            else:
                                bearer_token = token_result
                        except:
                            bearer_token = token_result
                    else:
                        # Assume it's the token itself
                        bearer_token = token_result
                else:
                    print(f"⚠️ [NEOFS] Unexpected bearer token result type: {type(token_result)}")
                    bearer_token = str(token_result) if token_result else None
                
                # Validate bearer token is actually a token (base64-like, no emojis)
                if bearer_token:
                    # Bearer tokens are typically base64, should be ASCII
                    # Remove any remaining emojis or non-ASCII if somehow they got through
                    import re
                    # Keep only ASCII alphanumeric and base64 characters
                    bearer_token_clean = re.sub(r'[^A-Za-z0-9+/=]', '', bearer_token)
                    
                    if len(bearer_token_clean) < 50:
                        print(f"❌ [NEOFS] Bearer token too short after cleaning: {len(bearer_token_clean)}")
                        raise ValueError(f"Bearer token appears invalid: {bearer_token[:100]}")
                    
                    bearer_token = bearer_token_clean
                    print(f"✅ [NEOFS] Bearer token obtained (length: {len(bearer_token)}, cleaned and ASCII-valid)")
                else:
                    raise ValueError("Bearer token creation returned empty result")
            except Exception as e:
                print(f"❌ [NEOFS] Failed to create bearer token: {e}")
                raise
        
        # Ensure container name is ASCII-only
        if not name.encode('ascii', errors='ignore').decode('ascii') == name:
            raise ValueError(f"Container name '{name}' contains non-ASCII characters")
        
        # Ensure all attribute values are ASCII-only strings
        if attributes:
            cleaned_attributes = {}
            for key, value in attributes.items():
                if not isinstance(value, str):
                    value = str(value)
                # Remove non-ASCII characters or encode them
                cleaned_value = value.encode('ascii', errors='ignore').decode('ascii')
                cleaned_attributes[key] = cleaned_value
            attributes = cleaned_attributes
        
        # Validate all parameters are ASCII before passing to tool
        print(f"📦 [NEOFS] Preparing container creation parameters...")
        print(f"   Container name: {name} (ASCII: {name.encode('ascii', errors='replace').decode('ascii') == name})")
        print(f"   Bearer token: {'SET' if bearer_token else 'NOT SET'} (length: {len(bearer_token) if bearer_token else 0})")
        if bearer_token:
            # Clean bearer token - remove any non-base64 characters
            import re
            bearer_token_clean = re.sub(r'[^A-Za-z0-9+/=]', '', bearer_token)
            
            if len(bearer_token_clean) < 50:
                print(f"   Bearer token too short after cleaning: {len(bearer_token_clean)}")
                raise ValueError(f"Bearer token appears invalid: {bearer_token[:100]}")
            
            bearer_token = bearer_token_clean
            print(f"   Bearer token cleaned and validated (length: {len(bearer_token)})")
        
        params = {
            "container_name": name,  # CreateContainerTool expects 'container_name', not 'name'
            "bearer_token": bearer_token,
            "basic_acl": basic_acl,
            "placement_policy": placement_policy
        }
        
        if attributes:
            params["attributes_json"] = json.dumps(attributes)
            print(f"   Attributes JSON: {params['attributes_json'][:100]}...")
        
        print(f"📦 [NEOFS] Calling create_container_tool.execute()...")
        try:
            result = await self.create_container_tool.execute(**params)
            output = result.output if hasattr(result, 'output') else result
            print(f"✅ [NEOFS] Container creation tool executed successfully")
            return output
        except Exception as e:
            error_msg = str(e)
            print(f"❌ [NEOFS] Container creation failed: {error_msg}")
            if "ASCII" in error_msg or "ascii" in error_msg.lower():
                print(f"   ⚠️  ASCII encoding error detected!")
                print(f"   Error details: {error_msg}")
                print(f"   Container name: {name}")
                print(f"   Container name (ASCII check): {name.encode('ascii', errors='replace').decode('ascii')}")
                print(f"   Bearer token (first 100 chars): {bearer_token[:100] if bearer_token else 'NONE'}...")
                if bearer_token:
                    try:
                        bearer_token.encode('ascii')
                        print(f"   Bearer token ASCII: ✅ Valid")
                    except UnicodeEncodeError as ascii_err:
                        print(f"   Bearer token ASCII: ❌ Invalid - {ascii_err}")
                print(f"   Attributes: {attributes}")
                print(f"   Owner address: {self.owner_address[:30] if self.owner_address else 'NOT SET'}...")
                print(f"   Private key set: {'YES' if self.private_key_wif else 'NO'}")
            import traceback
            traceback.print_exc()
            raise
    
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
