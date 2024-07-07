import subprocess
import re
import json
import enum


class ReadMode(enum.Enum):
    start = 0
    package_start = 1
    package_data = 2
    core_start = 3
    core_data = 4

class LinuxTemps(object):
    def __init__(self) -> None:
        self.__last_check_timestamp = 0
        self.__state_machine_step = 0
        self.__package_pos = 0
        self.__core_pos = 0
        self.__package = []
        self.__readmode = ReadMode.start
        self.__temp_unit = "ºC"

    def parse_output(self):
        data = subprocess.check_output("sensors -u 2> /dev/null", shell=True).strip().decode().split('\n')
        for line in data:
            if re.search("Package id (\d+):$",line):
                self.__readmode = ReadMode.package_start
                #print(f"Readmode = Package start")

            if re.search("Core (\d+)",line):
                self.__readmode = ReadMode.core_start
                #print(f"Readmode = Core start")

            if self.__readmode == ReadMode.package_start:
                self.__package_pos = int(re.search("Package id (\d+):$",line).group(1))
                if len(self.__package) <= self.__package_pos:
                    self.__package.append({'socket_number':self.__package_pos, 'cores':[]})
                    self.__readmode = ReadMode.package_data
                    self.__core_pos = 0
                    continue
            
            if self.__readmode == ReadMode.package_data:
                if re.search("temp\d+_input: (\d+\.\d+)$",line):
                    self.__package[self.__package_pos]['socket_temp_now'] = float(re.search("temp\d+_input: (\d+\.\d+)$",line).group(1))
                    continue
                if re.search("temp\d+_max: (\d+\.\d+)$",line):
                    self.__package[self.__package_pos]['socket_temp_high'] = float(re.search("temp\d+_max: (\d+\.\d+)$",line).group(1))
                    continue
                if re.search("temp\d+_crit: (\d+\.\d+)$",line):
                    self.__package[self.__package_pos]['socket_temp_critical'] = float(re.search("temp\d+_crit: (\d+\.\d+)$",line).group(1))
                    continue
                #No es ninguna de las anteriores, entonces es crit_alarm o alguna nueva que de momento no tenemos revisada
                continue

            if self.__readmode == ReadMode.core_start:
                self.__core_pos = int((re.search("Core (\d+):$",line)).group(1))
                if len(self.__package[self.__package_pos]['cores']) <= self.__core_pos:
                    self.__package[self.__package_pos]['cores'].append({'core_id':self.__core_pos})
                    self.__readmode = ReadMode.core_data
                    continue
            
            if self.__readmode == ReadMode.core_data:
                if re.search("temp\d+_input: (\d+\.\d+)$",line):
                    self.__package[self.__package_pos]['cores'][self.__core_pos]['core_temp_now'] = float(re.search("temp\d+_input: (\d+\.\d+)$",line).group(1))
                    continue
                if re.search("temp\d+_max: (\d+\.\d+)$",line):
                    self.__package[self.__package_pos]['cores'][self.__core_pos]['core_temp_high'] = float(re.search("temp\d+_max: (\d+\.\d+)$",line).group(1))
                    continue
                if re.search("temp\d+_crit: (\d+\.\d+)$",line):
                    self.__package[self.__package_pos]['cores'][self.__core_pos]['core_temp_critical'] = float(re.search("temp\d+_crit: (\d+\.\d+)$",line).group(1))
                    continue
                
                self.__readmode == ReadMode.start
                continue

        return self.__package


s = LinuxTemps()
cores = []
i = 0
for package in s.parse_output():
  for core in package['cores']:
    core['socket'] = package['socket_number']
    core['index'] = i
    cores.append(core)
    i += 1


print(json.dumps(cores))