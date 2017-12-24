import configparser


class Config:
    '''配置文件读取类'''

    '依据配置文件与SectionName返回配置的字典'
    @staticmethod
    def get_dict_by_section(conf_file, section_name):
        cf = configparser.ConfigParser()
        cf.read(conf_file)
        kv_list = cf.items(section_name)
        conf_dict = {}
        for item in kv_list:
            conf_dict[item[0]] = item[1]
        return conf_dict
