# tool_runner.py
from pydantic import BaseModel
import json
import os
from typing import Union
from toolbench.utils import standardize, change_name
import random

class Info(BaseModel):
    category: str
    tool_name: str
    api_name: str
    tool_input: Union[str, dict]
    strip: str

def prepare_tool_name_and_url(tools_root, info):
    category = info.category
    standard_category = category.replace(" ", "_").replace(",", "_").replace("/", "_")
    while " " in standard_category or "," in standard_category:
        standard_category = standard_category.replace(" ", "_").replace(",", "_")
    standard_category = standard_category.replace("__", "_")
    
    tool_name = info.tool_name
    api_name = change_name(standardize(info.api_name))
    if not tool_name.endswith(f"_for_{standard_category}"):
        tool_name = standardize(info.tool_name)
        code_string = f"""from {tools_root}.{standard_category}.{tool_name}.api import {api_name}"""
        tool_name += f"_for_{standard_category}"
    else:
        tmp_tool_name = standardize(tool_name.replace(f"_for_{standard_category}", ""))
        code_string = f"""from {tools_root}.{standard_category}.{tmp_tool_name}.api import {api_name}"""
    return tool_name, standard_category, api_name, code_string

def process_error(response):
    save_cache_flag = False
    switch_flag = False
    if "error" in str(response).lower():
        return_dict = {"error": "Message error...", "response": response}
    else:
        save_cache_flag = True
        return_dict = {"error": "", "response": response}
    return return_dict, save_cache_flag, switch_flag

def run(toolbench_code_string, toolbench_api_name, toolbench_input_params_str):
    success_flag = False
    switch_flag = False
    save_cache = False

    global_namespace = {}
    exec(toolbench_code_string, global_namespace)
    try:
        eval_func_str = f"{toolbench_api_name}({toolbench_input_params_str})"
        new_func = eval(eval_func_str, global_namespace)
        response, save_cache, switch_flag = process_error(new_func)
        success_flag = True
    except Exception as e:
        response = {"error": f"Function executing {toolbench_code_string} error...\n{e}", "response": ""}
        save_cache = False
    return success_flag, switch_flag, response, save_cache

def get_rapidapi_response(input_dict: dict, api_customization: bool=False, tools_root: str="data.toolenv.tools", schema_root: str="data/toolenv/response_examples"):
    info = Info(**{
        "category": input_dict['category'],
        "tool_name": input_dict['tool_name'],
        "api_name": input_dict['api_name'],
        "tool_input": input_dict['tool_input'],
        "strip": input_dict['strip']
    })
    rapidapi_key = input_dict['rapidapi_key']

    tool_name, standard_category, api_name, code_string = prepare_tool_name_and_url(tools_root, info)
    tool_input = info.tool_input
    
    try:
        tool_input = json.loads(tool_input)
    except Exception as e:
        tool_input = {}

    input_params_str = ""
    if len(tool_input) > 0:
        for key, value in tool_input.items():
            if isinstance(value, str):
                input_params_str += f'{key}="{value}", '
            else:
                input_params_str += f'{key}={value}, '
    if not api_customization:
        input_params_str += f"toolbench_rapidapi_key='{rapidapi_key}'"
    success_flag, switch_flag, response_dict, save_cache = run(code_string, api_name, input_params_str)
    return {"error": response_dict['error'], "response": str(response_dict['response'])[:2048]}