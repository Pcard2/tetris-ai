import binascii
import gspread

def decode_base64_padded(s, validate=True):
    # Add padding to the base64 string if necessary
    missing_padding = len(s) % 4
    if missing_padding:
        s += '=' * (4 - missing_padding)
    return binascii.a2b_base64(s, strict_mode=validate)

# Example usage with gspread
credentials = {
    "type": "service_account",
    "project_id": "tetris-tdr",
    "private_key_id": "5894339241a935a22bc8530dd935698eb570612f",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDIFe3wqbC6KlY8\nOodNRQPNEPlZiXzJyeVfS7lT/H5Gt8G9c1f507Lu24P+qZmx4ApNr5LyiHgbLYTq\nJLfCsLKIHEFP3PTSkJKG+Y+hjVZIKlZvIhe2j27J3LHeANg55FHM59lXO7U2IPxK\nY75HxBo9pimfBukDX6XiNt7D95irpCr56Nxdj98B4IkNAvoOWTozCh3hnRNT72Yf\nuKLl+8g5dOj4aS0C2QHH1bT2mlG+I1YJeDkZNAPfqGp1mG4yUqcoSbdfW1UQqhgw\nkPpdJAGTVXac3u8PXc5LdM42iUpKyEiA25ppv9+oE6uhi+2LjnFunUx5Fo4q54EW\ncKHQLGp7AgMBAAECggEAA8/LIyEQcVN6JhaVWkb8zgzLO0XvvyZd/MVECBIQ08cP\nZU0LuYIrb/p1lsXjXCyg9Z7pJT6tTxM8a3t8lrRoCkjDg8J5VYOUjwa1EkZPhPtt\nfxt+qSctXKIcL1cDx4KOfmFSViOYjanuNHqW9uYI+/Cs7U8j5EEPt3IFJ2WRnn9u\n/wezuMS9medFO0ZT8q5tjIH8kq5qQ2MKYHW/CSD1UWNDIgv+YCaC7tYBheiF4dj7\nBpUfqfGNNOUphfYDjKen//5UoJuOxRl/zvxVap3P+/O7bEAsziWw8/HX5J6dNXi9\n18BiZwgtJqNcaimYYYh5BRGJYUCknHVTj7/BpRmAsQKBgQDzBvHJHjp/RJ0M9riU\ntp2hladFuNL7yFk5nSBNqIvP12sAZnyV63U2D0XVTg35FFJBtry+Az9nWW2E28Sm\npY9iQyx6IZ0x7EzmAvMAk10jyv7DXElssnizhapbLjyjre3pwJys7POGSHUFtEYO\nMomVCYf987TXQGSBddH3jX3N8QKBgQDSxCyKYpvvwS+RTNIXN9+jFdfou89U/0XY\nIjK7yeUqPaBodJOduc85CrIK8NFI5r5X+bYznQlkjsQxIpXae2Tqip8CM1mWWH46\nLZaC+WcxFF3MyLbrloN7bIj4bCfHGE0HZxtSFGnjtxHFS0jWMmXWPCo7ZHeUcpKT\n9ngJH7EDKwKBgQCgufQIbfyEFQ3E+BsFB21i40W4X87xhAQ2jUtC8PheYfq7TgyR\nXiKruRgXRUMKez0XhtJ23FD/ee5rkqkRCae1dfWhZD/BN6V37XVm6Q8NUACDlbJd\nt/8Jw5nyKbcjDTGuiZtU5nT8V0lFl39JfnTtY1tUQexU+5o84H4XubT9EQKBgEpV\nmgfso2a50dcDKw25TQytxYp1wrgNmEqUNSR6HnL5bTup8e4s/GL33LdzG70EdJl+\nnr4xYoCuwY86zXNTFdKKtW4HQk9+QnauYWksITL0Jej12V3ZpeG/88b6DkVv0qsL\nuF0IihggFwpodPXmrHgUnCh6VJpsljnNMaS2Iq4lAoGAJCzvDUJXDXNvcCFWMHrH\nEpFw3LwNlB3VuXJoc5QFHX/tZvzOxMldfXzo7Xgfy3x4EGqA25DbBKHGfvlwWUqJ\na5IjlN2wXOdjOZ9Ks+VVc4fA1IcHqqCyvcSwfe89gYOCpTIBPhUw2H8T/47cP2GI\nwJEGfVeDPaVLjfdydfwpnQ8=\n-----END PRIVATE KEY-----\n",
    "client_email": "tetris-tdr@tetris-tdr.iam.gserviceaccount.com",
    "client_id": "100570209494388998451",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/tetris-tdr%40tetris-tdr.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}
gc = gspread.service_account_from_dict(credentials)

# Example base64 string with incorrect padding
s = "your_base64_string"

try:
    decoded_data = decode_base64_padded(s)
    print("Decoded data:", decoded_data)
except binascii.Error as e:
    print("Error decoding base64 string:", e)
