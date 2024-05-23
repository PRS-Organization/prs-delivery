def fill_template_with_dict(template, v_dict):
    # 使用字典来填充模板中的占位符, 假设模板中的占位符是 {key} 的形式，其中key是字典中的键
    return template.format_map(v_dict)


def information_description():
    template_string = "Find {name} and give the {color} {object} on the {receptacle} in the {location} to {name}."
    dict_information = {"name": "Alice", "object": "cup", "receptacle": "table", "location": "room", "color": 'red'}
    description = fill_template_with_dict(template_string, dict_information)
    print(description)

if __name__ == '__main__':
    information_description()
    exit(0)
    name = "Alice"
    day_type = "beautiful"
    filled_string = f"Hello, {name}! Today is a {day_type} day."
    print(filled_string)  # 输出: Hello, Alice! Today is a beautiful day.

    # 模板字符串，其中{name}和{day_type}是占位符
    templates = "Hello, {name}! Today is a {day_type} day."

    # 使用字典来提供要填充的值
    values_dict = {"name": "Alice", "day_type": "beautiful"}
    filled_string = fill_template_with_dict(templates, values_dict)
    print(filled_string)  # 输出: Hello, Alice! Today is a beautiful day.

    # 使用另一个字典来提供要填充的值
    values_dict_another = {"name": "Bob", "day_type": "sunny"}
    filled_string_another = fill_template_with_dict(templates, values_dict_another)
    print(filled_string_another)  # 输出: Hello, Bob! Today is a sunny day.

    # -----------------------------------------------------------------------------------


    def fill_template(template, *args):
        # 假设模板中的占位符数量与提供的参数数量相同
        return template.format(*args)


    # 模板字符串，其中{}是占位符
    template = "Hello, {}! Today is a {} day."

    # 使用不同的词来填充模板
    filled_string = fill_template(template, "Alice", "beautiful")
    print(filled_string)  # 输出: Hello, Alice! Today is a beautiful day.

    # 使用另外一组词来填充模板
    filled_string_another = fill_template(template, "Bob", "sunny")
    print(filled_string_another)  # 输出: Hello, Bob! Today is a sunny day.

