import configparser


def get_dict_by_section(conf_file, section_name):
    """
    依据配置文件与SectionName返回配置的字典
    :param conf_file:配置文件名称
    :param section_name:配置文件的section
    :return:该段的所有的option的字典
    """
    cf = configparser.ConfigParser()
    cf.read(conf_file)
    kv_list = cf.items(section_name)
    conf_dict = {}
    for item in kv_list:
        conf_dict[item[0]] = item[1]
    return conf_dict


debug_mode = int(get_dict_by_section("wx.conf","debug")['mode']) == 1
