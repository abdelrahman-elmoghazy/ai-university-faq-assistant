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
        
        # Generate dimension / 8 segments of 8 floats each using the hash
        # We'll just repeat the hash to fill the dimension
        vector = []
        while len(vector) < dimension:
            # Use chunks of the hash to create floats
            for i in range(0, len(h), 4):
                if len(vector) >= dimension:
                    break
                # Convert 4 bytes to a float between -1 and 1
                val = struct.unpack('!I', h[i:i+4])[0] / 4294967295.0
                vector.append(val * 2 - 1)
            # Re-hash the hash to get more "randomness"
            h = hashlib.sha256(h).digest()
            
        # Normalize the vector (for cosine similarity)
        norm = sum(x*x for x in vector)**0.5
        if norm > 0:
            vector = [x/norm for x in vector]
            
        return vector
