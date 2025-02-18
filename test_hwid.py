import subprocess

def obter_identificadores_hardware():
    try:
        # Obter UUID da placa-mãe
        uuid = subprocess.check_output("wmic csproduct get UUID", shell=True).decode().split("\n")[1].strip()

        # Obter Serial Number do disco rígido
        serial_number = subprocess.check_output("wmic diskdrive get SerialNumber", shell=True).decode().split("\n")[1].strip()

        # Obter MAC Address
        mac_output = subprocess.check_output("getmac /fo csv /nh", shell=True).decode()
        mac_address_raw = mac_output.split(",")[0].strip().strip('"')  # Remove aspas e espaços extras
        mac_address = mac_address_raw.replace("-", "")  # Remove os traços

        # Converter o MAC Address para o formato desejado
        formatted_mac = ":".join([mac_address[i:i+2] for i in range(0, len(mac_address), 2)])

        return f"{uuid}-{serial_number}-{formatted_mac}"
    except Exception as e:
        print(f"Erro ao obter identificadores de hardware: {e}")
        return None

if __name__ == "__main__":
    hwid = obter_identificadores_hardware()
    if hwid:
        print("HWID:", hwid)
    else:
        print("Falha ao obter HWID.")