from quantiphy import Quantity

def quantify_number(n):
    # Create a Quantity object with the number
    q = Quantity(n)
    # Return the formatted string
    return q

# Example usage
print(quantify_number(123456789))  # Output: 123M
