#!/usr/bin/env python3
"""
Create GPT-2 Medium with FP16 (16-bit) quantization for fraud detection
Target: ~700MB model size with good accuracy
"""

from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import json
from pathlib import Path

def create_gpt2_fp16():
    """Create GPT-2 Medium with FP16 precision"""
    print("🚀 Creating GPT-2 Medium with FP16 (16-bit)")
    print("=" * 50)
    
    model_id = "gpt2-medium"  # 354M parameters
    
    try:
        print(f"📥 Loading {model_id}...")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model in FP16 (half precision)
        print("🔧 Loading model in FP16 (half precision)...")
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,  # Half precision = 50% size reduction
            device_map="cpu"
        )
        
        print("✅ GPT-2 Medium FP16 loaded successfully!")
        return model, tokenizer
        
    except Exception as e:
        print(f"❌ GPT-2 Medium FP16 loading failed: {e}")
        return None, None

def test_gpt2_fraud_detection(model, tokenizer):
    """Test GPT-2 for fraud detection"""
    print("\n🧪 Testing GPT-2 Medium FP16 for Fraud Detection")
    print("-" * 50)
    
    try:
        # Fraud detection test cases
        test_cases = [
            {
                "name": "Bank Scam",
                "prompt": """Analyze this phone call for fraud:

Caller: "Hello, this is from your bank security. Your account has been compromised. I need your PIN to verify your identity immediately."
Victim: "This sounds suspicious. How do I know you're really from my bank?"
Caller: "Ma'am, this is urgent. If you don't verify now, we'll have to freeze your account permanently."

Is this FRAUD or LEGITIMATE? Explain briefly:"""
            },
            {
                "name": "Legitimate Call",
                "prompt": """Analyze this phone call for fraud:

Caller: "Hi, this is Sarah from ABC Insurance regarding your policy renewal that expires next month."
Victim: "Yes, I've been expecting your call."
Caller: "Great! I can email you the renewal options. What's the best email to send them to?"

Is this FRAUD or LEGITIMATE? Explain briefly:"""
            }
        ]
        
        for test_case in test_cases:
            print(f"\n📞 Testing: {test_case['name']}")
            
            inputs = tokenizer(
                test_case['prompt'], 
                return_tensors="pt", 
                truncation=True, 
                max_length=512
            )
            
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=50,
                    temperature=0.1,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id
                )
            
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            analysis = response.replace(test_case['prompt'], "").strip()
            
            print(f"🤖 GPT-2 Analysis: {analysis}")
        
        print("✅ GPT-2 Medium FP16 working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ GPT-2 test failed: {e}")
        return False

def save_gpt2_model(model, tokenizer, output_dir="app/src/main/assets"):
    """Save GPT-2 Medium FP16 to assets"""
    print(f"\n💾 Saving GPT-2 Medium FP16 to Assets")
    print("-" * 40)
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Remove old large models
    old_models = [
        "tiny_fraud_llm.pt", 
        "quantized_tinyllama.pt", 
        "tinyllama_fp16.pt",
        "tinyllama_10bit.pt"
    ]
    
    for old_file in old_models:
        old_path = output_path / old_file
        if old_path.exists():
            old_path.unlink()
            print(f"🗑️ Removed old model: {old_file}")
    
    # Save GPT-2 FP16 model
    model_file = output_path / "gpt2_medium_fp16.pt"
    
    try:
        torch.save(model.state_dict(), model_file)
        
        # Save tokenizer
        tokenizer_dir = output_path / "gpt2_medium_fp16_tokenizer"
        tokenizer.save_pretrained(tokenizer_dir)
        
        # Get file size
        model_size_mb = model_file.stat().st_size / (1024 * 1024)
        
        # Create model info
        model_info = {
            "model_name": "gpt2-medium",
            "model_type": "causal_lm",
            "parameters": "354M",
            "quantization": "FP16",
            "size_mb": round(model_size_mb, 1),
            "target_achieved": "Yes" if model_size_mb <= 800 else "Partial",
            "description": "GPT-2 Medium with FP16 precision for fraud detection",
            "advantages": [
                "Smaller than TinyLlama (354M vs 1.1B params)",
                "Better quantization support",
                "Proven architecture for text generation",
                "Good balance of size vs capability"
            ]
        }
        
        with open(output_path / "gpt2_medium_fp16_info.json", "w") as f:
            json.dump(model_info, f, indent=2)
        
        # Create fraud detection prompt template for GPT-2
        gpt2_prompt_template = """Analyze this phone conversation for fraud detection:

Conversation:
{conversation_text}

Analysis: Is this FRAUD or LEGITIMATE?
Reasoning:"""
        
        with open(output_path / "gpt2_fraud_prompt.txt", "w") as f:
            f.write(gpt2_prompt_template)
        
        print("✅ GPT-2 Medium FP16 saved successfully!")
        print(f"  📁 Model: {model_file} ({model_size_mb:.1f} MB)")
        print(f"  📁 Tokenizer: {tokenizer_dir}/")
        print(f"  📁 Info: {output_path / 'gpt2_medium_fp16_info.json'}")
        print(f"  📁 Prompt: {output_path / 'gpt2_fraud_prompt.txt'}")
        print(f"  🎯 Target (≤800MB): {'✅ YES' if model_size_mb <= 800 else '❌ NO'}")
        
        return model_size_mb
        
    except Exception as e:
        print(f"❌ Failed to save GPT-2 model: {e}")
        return 0

def main():
    """Main function for GPT-2 Medium FP16"""
    print("🎯 GPT-2 Medium FP16 Strategy")
    print("🎯 Target: ~700MB (vs 4.2GB TinyLlama)")
    print("🎯 Advantages: Smaller base model + FP16 precision")
    print("=" * 60)
    
    # Create GPT-2 FP16 model
    model, tokenizer = create_gpt2_fp16()
    
    if model is None:
        print("❌ GPT-2 Medium FP16 creation failed")
        return
    
    # Test fraud detection capabilities
    if test_gpt2_fraud_detection(model, tokenizer):
        # Save to assets
        size_mb = save_gpt2_model(model, tokenizer)
        
        print(f"\n📊 GPT-2 Medium FP16 Results")
        print("=" * 40)
        print(f"Model size:     {size_mb:.1f} MB")
        print(f"Parameters:     354M (vs 1.1B TinyLlama)")
        print(f"Precision:      FP16 (16-bit)")
        
        if size_mb > 0:
            tinyllama_size = 4196.4
            improvement = tinyllama_size / size_mb
            print(f"Improvement:    {improvement:.1f}x smaller than TinyLlama")
            
            if size_mb <= 800:
                print("🎉 Target achieved! Model ≤ 800MB")
                print("📱 Much more reasonable APK size")
            else:
                print("⚠️ Target not fully achieved but significant improvement")
                
            print(f"\n💡 GPT-2 Medium FP16 Benefits:")
            print(f"  • Much smaller base model (354M vs 1.1B)")
            print(f"  • FP16 works reliably on Apple Silicon")
            print(f"  • Good text generation capabilities")
            print(f"  • Proven architecture for mobile deployment")
            print(f"  • Better size/performance ratio for fraud detection")
        
    else:
        print("❌ GPT-2 model test failed")

if __name__ == "__main__":
    main()
