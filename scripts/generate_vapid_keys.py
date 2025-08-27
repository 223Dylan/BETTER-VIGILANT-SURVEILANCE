#!/usr/bin/env python3
"""
Generate VAPID keys for push notifications.

This script generates the necessary VAPID (Voluntary Application Server Identification)
keys for implementing web push notifications.

Usage:
    python scripts/generate_vapid_keys.py

Requirements:
    pip install pywebpush
"""

import os
import sys
from pathlib import Path

try:
    from pywebpush import WebPusher, WebPushException, generate_vapid_keypair
except ImportError:
    print("Error: pywebpush package not found.")
    print("Please install it first: pip install pywebpush")
    sys.exit(1)


def generate_keys():
    """Generate VAPID keypair."""
    try:
        print("Generating VAPID keys for push notifications...")

        # Generate the keypair
        vapid_keys = generate_vapid_keypair()

        print("\n" + "=" * 60)
        print("VAPID Keys Generated Successfully!")
        print("=" * 60)

        print(f"\nPublic Key (VAPID_PUBLIC_KEY):")
        print(f"{vapid_keys.public_key}")

        print(f"\nPrivate Key (VAPID_PRIVATE_KEY):")
        print(f"{vapid_keys.private_key}")

        print("\n" + "=" * 60)
        print("IMPORTANT: Add these to your environment variables:")
        print("=" * 60)

        print("\n# Add to your .env file or environment:")
        print(f"VAPID_PUBLIC_KEY={vapid_keys.public_key}")
        print(f"VAPID_PRIVATE_KEY={vapid_keys.private_key}")

        print("\n# For React frontend (.env file):")
        print(f"REACT_APP_VAPID_PUBLIC_KEY={vapid_keys.public_key}")

        print("\n# For production deployment:")
        print("# Set these as environment variables in your hosting platform")

        # Create .env.example file
        env_example_path = Path(".env.example")
        if not env_example_path.exists():
            with open(env_example_path, "w") as f:
                f.write("# VAPID Keys for Push Notifications\n")
                f.write(f"VAPID_PUBLIC_KEY={vapid_keys.public_key}\n")
                f.write(f"VAPID_PRIVATE_KEY={vapid_keys.private_key}\n")
                f.write("\n# Frontend VAPID Public Key\n")
                f.write(f"REACT_APP_VAPID_PUBLIC_KEY={vapid_keys.public_key}\n")

            print(f"\n✅ Created .env.example file with the keys")

        print("\n" + "=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print("1. Add the keys to your environment variables")
        print("2. Restart your backend server")
        print("3. Test push notifications in your browser")
        print("4. Keep the private key secure and never expose it publicly")

        return True

    except Exception as e:
        print(f"Error generating VAPID keys: {e}")
        return False


def test_keys():
    """Test the generated keys with a sample subscription."""
    try:
        print("\n" + "=" * 60)
        print("Testing VAPID Keys...")
        print("=" * 60)

        # This would require a real subscription to test
        print("To test the keys:")
        print("1. Start your application")
        print("2. Navigate to the Push Settings tab")
        print("3. Grant notification permission")
        print("4. Subscribe to push notifications")
        print("5. Send a test notification")

        return True

    except Exception as e:
        print(f"Error testing keys: {e}")
        return False


def main():
    """Main function."""
    print("VAPID Key Generator for Push Notifications")
    print("=" * 50)

    # Generate keys
    if generate_keys():
        # Test keys
        test_keys()

        print("\n" + "=" * 60)
        print("✅ VAPID keys generated successfully!")
        print("=" * 60)
    else:
        print("\n❌ Failed to generate VAPID keys")
        sys.exit(1)


if __name__ == "__main__":
    main()
