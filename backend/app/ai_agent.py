import os
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from io import BytesIO
import json
from openai import OpenAI
from anthropic import Anthropic

class DataAnalysisAgent:
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        if provider == "openai":
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            self.model = "gpt-4o"
        else:
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            self.model = "claude-3-5-sonnet-20241022"
        
        self.action_log = []
        self.generated_files = []
    
    def process_request(self, message: str, df: pd.DataFrame) -> Tuple[str, List[Dict[str, Any]], List[str]]:
        self.action_log = []
        self.generated_files = []
        
        system_prompt = """You are a data analysis assistant. You have access to tools to analyze and manipulate data.
Always inspect the data first before performing operations.
Explain each step clearly in plain English.
Never hallucinate column names - only use columns that exist in the dataframe.
Be precise and accurate in your analysis."""

        tools = self._get_tools()
        
        messages = [
            {"role": "user", "content": f"Here's what I need: {message}\n\nThe dataframe has shape {df.shape} with columns: {list(df.columns)}"}
        ]
        
        if self.provider == "openai":
            response = self._process_openai(messages, tools, df, system_prompt)
        else:
            response = self._process_anthropic(messages, tools, df, system_prompt)
        
        return response, self.generated_files, self.action_log
    
    def _get_tools(self) -> List[Dict]:
        return [
            {
                "type": "function",
                "function": {
                    "name": "inspect_data",
                    "description": "Inspect the dataframe to see its structure, columns, data types, and sample rows",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "num_rows": {"type": "integer", "description": "Number of sample rows to view", "default": 5}
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "clean_data",
                    "description": "Clean the data by handling missing values, removing duplicates, or standardizing formats",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "operations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of cleaning operations: 'drop_na', 'fill_na', 'drop_duplicates', 'strip_whitespace'"
                            }
                        },
                        "required": ["operations"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "dedupe",
                    "description": "Remove duplicate rows from the dataframe",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "subset": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Columns to consider for identifying duplicates. If empty, use all columns"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "detect_outliers",
                    "description": "Detect outliers in numeric columns using IQR method",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "column": {"type": "string", "description": "Column name to check for outliers"}
                        },
                        "required": ["column"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "aggregate",
                    "description": "Aggregate data using group by operations",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "group_by": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Columns to group by"
                            },
                            "agg_column": {"type": "string", "description": "Column to aggregate"},
                            "agg_func": {"type": "string", "description": "Aggregation function: sum, mean, count, min, max"}
                        },
                        "required": ["group_by", "agg_column", "agg_func"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "pivot",
                    "description": "Create a pivot table from the data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "index": {"type": "string", "description": "Column to use as index"},
                            "columns": {"type": "string", "description": "Column to use as columns"},
                            "values": {"type": "string", "description": "Column to aggregate"},
                            "aggfunc": {"type": "string", "description": "Aggregation function", "default": "sum"}
                        },
                        "required": ["index", "columns", "values"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "plot",
                    "description": "Create a visualization of the data",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "plot_type": {"type": "string", "description": "Type of plot: bar, line, scatter, hist"},
                            "x_column": {"type": "string", "description": "Column for x-axis"},
                            "y_column": {"type": "string", "description": "Column for y-axis (not needed for hist)"},
                            "title": {"type": "string", "description": "Plot title"}
                        },
                        "required": ["plot_type"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "export_csv",
                    "description": "Export the current dataframe as CSV",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Name for the exported file"}
                        },
                        "required": ["filename"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "export_xlsx",
                    "description": "Export the current dataframe as Excel file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {"type": "string", "description": "Name for the exported file"}
                        },
                        "required": ["filename"]
                    }
                }
            }
        ]
    
    def _process_openai(self, messages: List[Dict], tools: List[Dict], df: pd.DataFrame, system_prompt: str) -> str:
        max_iterations = 10
        current_df = df.copy()
        
        for iteration in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}] + messages,
                tools=tools,
                tool_choice="auto"
            )
            
            assistant_message = response.choices[0].message
            messages.append(assistant_message.model_dump())
            
            if not assistant_message.tool_calls:
                return assistant_message.content
            
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                result, current_df = self._execute_tool(function_name, function_args, current_df)
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        
        return "Analysis complete. Check the action log for details."
    
    def _process_anthropic(self, messages: List[Dict], tools: List[Dict], df: pd.DataFrame, system_prompt: str) -> str:
        max_iterations = 10
        current_df = df.copy()
        
        anthropic_tools = []
        for tool in tools:
            anthropic_tools.append({
                "name": tool["function"]["name"],
                "description": tool["function"]["description"],
                "input_schema": tool["function"]["parameters"]
            })
        
        for iteration in range(max_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=messages,
                tools=anthropic_tools
            )
            
            if response.stop_reason == "end_turn":
                text_content = ""
                for block in response.content:
                    if block.type == "text":
                        text_content += block.text
                return text_content
            
            messages.append({
                "role": "assistant",
                "content": response.content
            })
            
            if response.stop_reason == "tool_use":
                tool_results = []
                
                for block in response.content:
                    if block.type == "tool_use":
                        function_name = block.name
                        function_args = block.input
                        
                        result, current_df = self._execute_tool(function_name, function_args, current_df)
                        
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result
                        })
                
                messages.append({
                    "role": "user",
                    "content": tool_results
                })
        
        return "Analysis complete. Check the action log for details."
    
    def _execute_tool(self, function_name: str, args: Dict, df: pd.DataFrame) -> Tuple[str, pd.DataFrame]:
        self.action_log.append(f"Executing: {function_name} with args {args}")
        
        if function_name == "inspect_data":
            return self._inspect_data(df, args.get("num_rows", 5)), df
        elif function_name == "clean_data":
            return self._clean_data(df, args["operations"])
        elif function_name == "dedupe":
            return self._dedupe(df, args.get("subset", []))
        elif function_name == "detect_outliers":
            return self._detect_outliers(df, args["column"]), df
        elif function_name == "aggregate":
            return self._aggregate(df, args["group_by"], args["agg_column"], args["agg_func"])
        elif function_name == "pivot":
            return self._pivot(df, args["index"], args["columns"], args["values"], args.get("aggfunc", "sum"))
        elif function_name == "plot":
            return self._plot(df, args), df
        elif function_name == "export_csv":
            return self._export_csv(df, args["filename"]), df
        elif function_name == "export_xlsx":
            return self._export_xlsx(df, args["filename"]), df
        else:
            return f"Unknown function: {function_name}", df
    
    def _inspect_data(self, df: pd.DataFrame, num_rows: int) -> str:
        info = f"Shape: {df.shape}\n"
        info += f"Columns: {list(df.columns)}\n"
        info += f"Data types:\n{df.dtypes}\n"
        info += f"\nFirst {num_rows} rows:\n{df.head(num_rows).to_string()}\n"
        info += f"\nBasic statistics:\n{df.describe()}"
        return info
    
    def _clean_data(self, df: pd.DataFrame, operations: List[str]) -> Tuple[str, pd.DataFrame]:
        result_df = df.copy()
        results = []
        
        for op in operations:
            if op == "drop_na":
                before = len(result_df)
                result_df = result_df.dropna()
                results.append(f"Dropped {before - len(result_df)} rows with missing values")
            elif op == "fill_na":
                result_df = result_df.fillna(0)
                results.append("Filled missing values with 0")
            elif op == "drop_duplicates":
                before = len(result_df)
                result_df = result_df.drop_duplicates()
                results.append(f"Dropped {before - len(result_df)} duplicate rows")
            elif op == "strip_whitespace":
                for col in result_df.select_dtypes(include=['object']).columns:
                    result_df[col] = result_df[col].str.strip()
                results.append("Stripped whitespace from text columns")
        
        return "\n".join(results), result_df
    
    def _dedupe(self, df: pd.DataFrame, subset: List[str]) -> Tuple[str, pd.DataFrame]:
        before = len(df)
        result_df = df.drop_duplicates(subset=subset if subset else None)
        return f"Removed {before - len(result_df)} duplicate rows. New shape: {result_df.shape}", result_df
    
    def _detect_outliers(self, df: pd.DataFrame, column: str) -> str:
        if column not in df.columns:
            return f"Column '{column}' not found in dataframe"
        
        try:
            data = pd.to_numeric(df[column], errors='coerce').dropna()
            Q1 = data.quantile(0.25)
            Q3 = data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = data[(data < lower_bound) | (data > upper_bound)]
            
            return f"Found {len(outliers)} outliers in column '{column}'\nLower bound: {lower_bound}\nUpper bound: {upper_bound}\nOutlier values: {outliers.values[:10]}"
        except Exception as e:
            return f"Error detecting outliers: {str(e)}"
    
    def _aggregate(self, df: pd.DataFrame, group_by: List[str], agg_column: str, agg_func: str) -> Tuple[str, pd.DataFrame]:
        try:
            result_df = df.groupby(group_by)[agg_column].agg(agg_func).reset_index()
            return f"Aggregated data by {group_by}. Result shape: {result_df.shape}\n{result_df.to_string()}", result_df
        except Exception as e:
            return f"Error aggregating: {str(e)}", df
    
    def _pivot(self, df: pd.DataFrame, index: str, columns: str, values: str, aggfunc: str) -> Tuple[str, pd.DataFrame]:
        try:
            result_df = pd.pivot_table(df, index=index, columns=columns, values=values, aggfunc=aggfunc).reset_index()
            return f"Created pivot table. Result shape: {result_df.shape}\n{result_df.to_string()}", result_df
        except Exception as e:
            return f"Error creating pivot: {str(e)}", df
    
    def _plot(self, df: pd.DataFrame, args: Dict) -> str:
        try:
            plot_type = args["plot_type"]
            x_col = args.get("x_column")
            y_col = args.get("y_column")
            title = args.get("title", "Data Visualization")
            
            plt.figure(figsize=(10, 6))
            
            if plot_type == "bar" and x_col and y_col:
                df_plot = df[[x_col, y_col]].dropna()
                plt.bar(df_plot[x_col], df_plot[y_col])
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            elif plot_type == "line" and x_col and y_col:
                df_plot = df[[x_col, y_col]].dropna()
                plt.plot(df_plot[x_col], df_plot[y_col])
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            elif plot_type == "scatter" and x_col and y_col:
                df_plot = df[[x_col, y_col]].dropna()
                plt.scatter(df_plot[x_col], df_plot[y_col])
                plt.xlabel(x_col)
                plt.ylabel(y_col)
            elif plot_type == "hist" and x_col:
                df_plot = df[x_col].dropna()
                plt.hist(df_plot, bins=20)
                plt.xlabel(x_col)
                plt.ylabel("Frequency")
            else:
                return "Invalid plot configuration"
            
            plt.title(title)
            plt.tight_layout()
            
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            plt.close()
            
            file_id = f"plot_{len(self.generated_files)}.png"
            self.generated_files.append({
                "file_id": file_id,
                "filename": f"{title.replace(' ', '_')}.png",
                "content": buf.getvalue(),
                "type": "image/png"
            })
            
            return f"Created {plot_type} plot: {title}"
        except Exception as e:
            return f"Error creating plot: {str(e)}"
    
    def _export_csv(self, df: pd.DataFrame, filename: str) -> str:
        try:
            csv_buffer = BytesIO()
            df.to_csv(csv_buffer, index=False)
            csv_buffer.seek(0)
            
            if not filename.endswith('.csv'):
                filename += '.csv'
            
            file_id = f"export_{len(self.generated_files)}.csv"
            self.generated_files.append({
                "file_id": file_id,
                "filename": filename,
                "content": csv_buffer.getvalue(),
                "type": "text/csv"
            })
            
            return f"Exported data to {filename} ({len(df)} rows, {len(df.columns)} columns)"
        except Exception as e:
            return f"Error exporting CSV: {str(e)}"
    
    def _export_xlsx(self, df: pd.DataFrame, filename: str) -> str:
        try:
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_buffer.seek(0)
            
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            
            file_id = f"export_{len(self.generated_files)}.xlsx"
            self.generated_files.append({
                "file_id": file_id,
                "filename": filename,
                "content": excel_buffer.getvalue(),
                "type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            })
            
            return f"Exported data to {filename} ({len(df)} rows, {len(df.columns)} columns)"
        except Exception as e:
            return f"Error exporting Excel: {str(e)}"
