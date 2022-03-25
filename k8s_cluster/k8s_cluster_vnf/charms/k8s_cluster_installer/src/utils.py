import string
import secrets
from typing import Dict

def generate_random_k8s_compliant_hostname(current_hostname: str, maximum_size=63) -> str:
    """Generate a both unique and human readable k8s hostname compliant with k8s Label Names requirements 
    (https://kubernetes.io/docs/concepts/overview/working-with-objects/names/#rfc-1035-label-names), which in 
    turn follows the RFC 1035 (https://datatracker.ietf.org/doc/html/rfc1035)

    Args:
        current_hostname (str): current human readable node's hostname

    Returns:
        str: the new unique hostname
    """

    def remove_start_end_non_accepted(s: str):
        if s[0] == '-':
            s = remove_start_end_non_accepted(s[1:])
        if s[len(s) - 1] == '-':
            s = remove_start_end_non_accepted(s[:len(s) - 1])
        return s
    
    # string with 8 alphanumeric chars (62**8=218340105584896 possible combinations)
    current_random_value = ''.join(secrets.choice(string.ascii_letters + string.digits) for i in range(8))
    inter_result = remove_start_end_non_accepted(
        f"{current_hostname.replace('_', '-')[:maximum_size-len(current_random_value)]}-{current_random_value}")
    
    result = ""
    for i in range(len(inter_result)):
        ch = inter_result[i]
        if ch.isalnum() or ch == '-':
            result += ch
            
    return result


# TODO -> REMOVE THIS WHEN N2VC FIX IS ACCEPTED (another charm, just for the interactions with the operator's OSM NBI)
def create_new_file_from_template(template: str, new_file: str, replacements: Dict[str, str]) -> None:
    """Create a new local file from a template one, where you want to substitute the original content of the template
       with certain values

    Args:
        template (str): Template file
        new_file (str): New file to be created from the template
        replacements (Dict[str, str]): A dictionary with the replacements to conduct in the new file. The keys shall be
                                       the original values, and the corresponding values shall be the replacement for
                                       that original value.
    """
    
    with open(template, 'r') as file:
        file_content = file.read()
        
    new_file_content = file_content
    for original in replacements:
        new_file_content = new_file_content.replace(original, replacements[original])
        
    with open(new_file, 'w') as file:
        file.write(new_file_content)
