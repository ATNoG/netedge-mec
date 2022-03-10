import string
import secrets

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
 