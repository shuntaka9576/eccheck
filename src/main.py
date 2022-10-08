from cryptoauthlib import (atcab_info, atcab_init, atcab_read_config_zone,
                           atcab_read_serial_number, cfg_ateccx08a_i2c_default)
from cryptoauthlib.library import load_cryptoauthlib

ATCA_SUCCESS = 0x00
BLOCK_SIZE = 32


class Ecc608:
    def __init__(self):
        ECC608_I2C_ADDRESS = 0xC0
        RPI_I2C_BUS = 3

        load_cryptoauthlib()

        cfg = cfg_ateccx08a_i2c_default()
        cfg.cfg.atcai2c.slave_address = ECC608_I2C_ADDRESS
        cfg.cfg.atcai2c.bus = RPI_I2C_BUS

        init_result = atcab_init(cfg)

        if not init_result == ATCA_SUCCESS:
            raise Exception("init config exception")

        # get info
        info = bytearray(4)
        get_info_result = atcab_info(info)

        if get_info_result == ATCA_SUCCESS and info is not None:
            self.__info = info
        else:
            raise Exception("init info exception")

        # get serial number
        serial_number = bytearray(9)
        get_read_serial_number_result = atcab_read_serial_number(serial_number)

        if get_read_serial_number_result == ATCA_SUCCESS and serial_number is not None:
            self.__serial_number = serial_number
        else:
            raise Exception("init serial number exception")

        # get config zone
        config_zone = bytearray(128)
        get_read_config_zone_result = atcab_read_config_zone(config_zone)

        if get_read_config_zone_result == ATCA_SUCCESS and config_zone is not None:
            self.config_zone = config_zone

        else:

            raise Exception("get config zone exception")

    def get_serial_number(self):
        return self.convert_to_string_from_bytearray(self.__serial_number)

    def convert_to_string_from_bytearray(self, a):
        lines = []
        for x in range(0, len(a)):
            lines.append("{:02X}".format(a[x]))

        return "".join(lines)


def main():
    ecc608 = Ecc608()
    print(f"serial_number: {ecc608.get_serial_number()}")


if __name__ == "__main__":
    main()
