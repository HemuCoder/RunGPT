"""Tool Injector - 工具描述注入器"""
from typing import Optional


class ToolInjector:
    """工具描述生成器"""
    
    def generate_react_format(self, tools) -> str:
        """生成 ReAct 格式的工具描述（包含参数信息）"""
        if not tools or not hasattr(tools, 'list_tools'):
            return "可用工具：无"
        
        tool_names = tools.list_tools()
        if not tool_names:
            return "可用工具：无"
        
        desc = "可用工具：\n"
        for name in tool_names:
            tool = tools.get_tool(name)
            if tool:
                # 工具名称和描述
                desc += f"\n{name}"
                if tool.description:
                    desc += f": {tool.description}"
                desc += "\n"
                
                # 参数信息
                params = tool.parameters
                if params:
                    required_params = []
                    optional_params = []
                    
                    for param_name, param_info in params.items():
                        if param_name == "__doc__":
                            continue
                        
                        param_type = param_info.get('type', 'string')
                        is_required = param_info.get('required', True)
                        
                        if is_required:
                            required_params.append(f"{param_name}: {param_type}")
                        else:
                            default = param_info.get('default', 'None')
                            optional_params.append(f"{param_name}: {param_type} = {default}")
                    
                    if required_params or optional_params:
                        desc += "  参数: "
                        all_params = required_params + optional_params
                        desc += ", ".join(all_params)
                        desc += "\n"
        
        desc += "\n使用格式：Action: tool_name(param_name=\"value\")"
        desc += "\n示例：Action: calculator(expression=\"100+200\")"
        return desc

