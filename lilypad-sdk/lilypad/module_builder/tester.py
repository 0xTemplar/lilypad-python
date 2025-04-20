# Usage example
if __name__ == "__main__":
    from lilypad.module_builder import LilypadModuleBuilder, ModuleConfig, ModulePublisher
    
    config = ModuleConfig(
        module_name="my-llm",
        module_version="1.0.0",
        model_repo="tiiuae/falcon-7b-instruct",
        gpu=True,
        environment_vars=["MODEL_INPUT"]
    )
    
    builder = (
        LilypadModuleBuilder(config)
        .create_directory_structure()
        .generate_dockerfile()
        .generate_manifest()
        .add_dependencies(["transformers", "torch"])
        .add_model_download_script()
        .create_inference_template()
    )
    
    publisher = ModulePublisher(builder)
    
    # Test locally
    test_result = publisher.run_local_test({
        "MODEL_INPUT": "Explain quantum computing"
    })
    print("Local test result:", test_result)
    
    # Deploy to network
    cid = publisher.deploy_to_lilypad()
    print(f"Module deployed successfully! CID: {cid}")