import urllib.parse
import logging

logger = logging.getLogger(__name__)

def parse_uri_command(uri_string):
    """
    Parses a custom URI string, handling both standard (://) and custom (:) formats.
    
    Standard: tapeciarnia://setwallpaper?url=...
    Custom 1: tapeciarnia:https://image.jpg
    Custom 2: tapeciarnia:mp4_url:https://video.mp4

    Args:
        uri_string (str): The full URI string passed from the OS.

    Returns:
        tuple: (action_name, params_dict) or (None, None) on failure.
    """
    try:
        # 1. Parse the entire URL to get scheme and components
        parsed_uri = urllib.parse.urlparse(uri_string)
        
        # Check if the scheme is correct
        if parsed_uri.scheme != 'tapeciarnia':
            logger.warning(f"URI scheme mismatch: Expected 'tapeciarnia', got '{parsed_uri.scheme}'")
            return None, None
            
        action = None
        params = {}

        # --- Handling the new custom format (tapeciarnia:payload or tapeciarnia:action:payload) ---
        # This format is identified when netloc and query are empty, and the path contains the command.
        if not parsed_uri.netloc and not parsed_uri.query and parsed_uri.path:
            payload = parsed_uri.path.strip()
            
            # Case 1: tapeciarnia:ACTION:PAYLOAD (e.g., tapeciarnia:mp4_url:https://...)
            # We look for a colon ONLY if the payload doesn't look like a standard URL itself (i.e., not starting with 'http')
            if ':' in payload and not payload.lower().startswith('http'):
                parts = payload.split(':', 1)
                action = parts[0].strip()
                params = {'url': parts[1].strip()}
            
            # Case 2: tapeciarnia:PAYLOAD (e.g., tapeciarnia:https://...)
            else:
                # Default action for direct image/file URLs
                action = "set_url_default" 
                # If the URL ends in mp4, we can set the action to mp4_url for consistency
                if payload.lower().endswith(('.mp4', '.webm', '.mov')):
                    action = "mp4_url"
                    
                params = {'url': payload.strip()}
                
            logger.info(f"Successfully parsed CUSTOM URI. Action: {action}, Params: {params}")
            return action, params


        # --- Handling the old standard format (tapeciarnia://action?param=value) ---
        
        # 2. Extract the action from path component (removing leading '/')
        action = parsed_uri.path.strip('/')
        
        # CRITICAL FIX for standard format: If the path is empty, the action was likely misinterpreted as the netloc 
        # (e.g., in "tapeciarnia://setwallpaper?url=..."). Use the netloc (authority) as the action if the path is empty.
        if not action and parsed_uri.netloc:
            action = parsed_uri.netloc.split('@')[-1].split(':')[0]
            
        # 3. Parse query parameters (only applicable to standard format)
        query_params = urllib.parse.parse_qs(parsed_uri.query)
        
        # Convert list values to single string values (assuming single values for parameters)
        params = {k: v[0] for k, v in query_params.items()}

        logger.info(f"Successfully parsed STANDARD URI. Action: {action}, Params: {params}")
        
        return action, params

    except Exception as e:
        logger.error(f"Failed to parse URI '{uri_string}': {e}")
        return None, None
    
if __name__ == "__main__":

    action , param  = parse_uri_command("tapeciarnia:https://netplus.pl/comfyui/tmp/16692.jpg")
    print(action,param)