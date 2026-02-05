from langchain.agents.middleware import wrap_model_call, ModelRequest, ModelResponse


# 1. 定义一个工厂函数，接收你想动态传入的模型
def create_dynamic_selector(basic_llm, advanced_llm, threshold=10):
    # 2. 在内部定义中间件，并加上装饰器
    @wrap_model_call
    def dynamic_model_selection(request: ModelRequest, handler) -> ModelResponse:
        """Choose model based on conversation complexity."""
        # 这里可以直接使用外部传入的 basic_llm 和 advanced_llm
        message_count = len(request.state["messages"])

        if message_count > threshold:
            print(f"Messages count {message_count} > {threshold}, switching to Advanced Model.")
            selected_model = advanced_llm
        else:
            print(f"Using Basic Model.")
            selected_model = basic_llm

        return handler(request.override(model=selected_model))

    # 3. 返回配置好的中间件函数
    return dynamic_model_selection