import hashlib
import struct
from typing import List

class EmbeddingService:
    @staticmethod
    def generate_embedding(text: str, dimension: int = 384) -> List[float]:
        """
        Generate a deterministic mock embedding from text.
        This ensures that similar text has stable vectors for demonstration.
        """
        # Create a hash of the text
        h = hashlib.sha256(text.encode('utf-8')).digest()
        
        vector = []
        while len(vector) < dimension:
            for i in range(0, len(h), 4):
                if len(vector) >= dimension:
                    break
                val = struct.unpack('!I', h[i:i+4])[0] / 4294967295.0
                vector.append(val * 2 - 1)
            h = hashlib.sha256(h).digest()
            
        norm = sum(x*x for x in vector)**0.5
        if norm > 0:
            vector = [x/norm for x in vector]
            
        return vector
