import os
import argparse
import datahelper
from dotenv import load_dotenv

def run_test(file_path: str, question: str, llm_to_test: str):
    """
    一个用于直接测试 datahelper.ask_question 函数的脚本。
    通过命令行参数接收文件路径、问题和要使用的 LLM。
    """
    # 加载环境变量 (确保 DEEPSEEK_API_URL 和 GOOGLE_API_KEY 已设置)
    load_dotenv()
    print("--- 环境变量加载完毕 ---")

    # 设置要使用的 LLM
    try:
        datahelper.set_llm(llm_to_test)
        print(f"--- 使用 LLM: {llm_to_test} ---")
    except ValueError as e:
        print(f"错误：无法设置 LLM。{e}")
        return

    # 检查测试文件是否存在
    if not os.path.exists(file_path):
        print(f"错误：测试文件未找到，请检查路径：{file_path}")
        print("提示：请将您的测试数据文件（如 充值数据.csv）放入 'data' 文件夹中，或使用 '--file_path' 参数指定正确路径。")
        return
    
    print(f"--- 使用测试文件: {file_path} ---")
    print(f"--- 测试问题: {question} ---")

    print("\n--- 开始调用 ask_question 并打印流式输出 ---")
    try:
        # 调用函数并获取生成器
        response_generator = datahelper.ask_question(file_path, question)

        full_response = ""
        # 遍历生成器的每一部分并打印
        for chunk in response_generator:
            # Agent 的流式输出是一个字典，我们只关心 'output' 键
            if "output" in chunk:
                print(chunk["output"], end="", flush=True)
                full_response += chunk["output"]

        print("\n\n--- 流式输出结束 ---")
        
        # 检查最终回复是否包含错误信息
        if "parsing failure" in full_response.lower() or "invalid or incomplete response" in full_response.lower():
            print("\n--- 检测到 Agent 输出解析错误 ---")
            print("这通常意味着 Agent 未能正确格式化其最终答案。")
            print("完整的原始输出如下，以供调试：")
        else:
            print("\n--- 完整的最终回复 ---")

        print(full_response)
        print("\n--- 测试结束 ---")

    except Exception as e:
        print(f"\n--- 测试过程中发生异常 ---")
        print(f"异常类型: {type(e).__name__}")
        print(f"异常信息: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行数据分析 Agent 测试脚本")
    parser.add_argument(
        "--file_path", 
        type=str, 
        default="data/变现群小机器人收入数据.csv",
        help="要分析的 CSV 文件的路径"
    )
    parser.add_argument(
        "--question", 
        type=str, 
        default="哪天总收入最高？并分析下原因",
        help="要向 Agent 提的问题"
    )
    parser.add_argument(
        "--llm",
        type=str,
        default="Deepseek",
        choices=["Deepseek", "Gemini"],
        help="要使用的 LLM ('Deepseek' 或 'Gemini')"
    )
    
    args = parser.parse_args()
    
    run_test(args.file_path, args.question, args.llm) 