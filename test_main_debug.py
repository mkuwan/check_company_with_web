#!/usr/bin/env python3
# Test if main.py can be executed with debug output
import sys
import os
sys.path.append(os.path.dirname(__file__))

try:
    # Override sys.argv to provide test arguments
    sys.argv = [
        'main.py',
        '--company', '株式会社テスト', 
        '--address', '東京都新宿区1-1-1',
        '--tel', '03-9999-9999'
    ]
    
    print("Starting main.py test...")
    import main
    
    print("Calling main function...")
    main.main()
    print("main function completed successfully!")
    
except Exception as e:
    print(f"Error occurred: {e}")
    import traceback
    traceback.print_exc()
