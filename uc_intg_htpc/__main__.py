"""Allow running as python -m uc_intg_htpc."""

import asyncio

from uc_intg_htpc import main

if __name__ == "__main__":
    asyncio.run(main())
