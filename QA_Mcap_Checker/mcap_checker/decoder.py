#!/usr/bin/env python3
"""
Message decoder - supports ROS2 message formats.
"""

import struct
from typing import Optional, Dict, Any, List


class CDRDecoder:
    """
    CDR (Common Data Representation) decoder.
    Used to parse ROS2 messages.
    """
    
    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0
        
        # Read CDR header (4 bytes)
        if len(data) >= 4:
            self.pos = 4
    
    def read_uint32(self) -> int:
        """Read uint32."""
        if self.pos + 4 > len(self.data):
            return 0
        value = struct.unpack_from('<I', self.data, self.pos)[0]
        self.pos += 4
        return value
    
    def read_float64(self) -> float:
        """Read float64 (double)."""
        if self.pos + 8 > len(self.data):
            return 0.0
        value = struct.unpack_from('<d', self.data, self.pos)[0]
        self.pos += 8
        return value
    
    def read_string(self) -> str:
        """Read a UTF-8 string."""
        length = self.read_uint32()
        if self.pos + length > len(self.data):
            return ""
        value = self.data[self.pos:self.pos + length].decode('utf-8', errors='ignore')
        self.pos += length
        # Align to 4-byte boundary
        self.pos = (self.pos + 3) & ~3
        return value.rstrip('\x00')
    
    def read_sequence_header(self) -> int:
        """Read sequence header (return sequence length)."""
        return self.read_uint32()


def decode_joint_state(data: bytes) -> Optional[Dict[str, Any]]:
    """
    Decode a sensor_msgs/msg/JointState message.

    JointState structure:
    - std_msgs/Header header
    - string[] name
    - float64[] position
    - float64[] velocity
    - float64[] effort
    """
    try:
        decoder = CDRDecoder(data)
        
        result = {}
        
        # Read Header
        # Header.stamp: int32 sec + uint32 nanosec = 8 bytes
        decoder.pos += 8
        
        # Header.frame_id: string (length + data + padding)
        frame_id_len = decoder.read_uint32()
        if frame_id_len > 0:
            decoder.pos += frame_id_len
            # Align to 4-byte boundary
            decoder.pos = (decoder.pos + 3) & ~3
        
        # Read name[] (string array)
        name_count = decoder.read_sequence_header()
        names = []
        for _ in range(name_count):
            name_len = decoder.read_uint32()
            if name_len > 0 and decoder.pos + name_len <= len(data):
                name = data[decoder.pos:decoder.pos + name_len].decode('utf-8', errors='ignore').rstrip('\x00')
                decoder.pos += name_len
                decoder.pos = (decoder.pos + 3) & ~3
                names.append(name)
        result['name'] = names
        
        # Read position[] (float64 array)
        pos_count = decoder.read_sequence_header()
        positions = []
        for _ in range(pos_count):
            if decoder.pos + 8 <= len(data):
                positions.append(decoder.read_float64())
        result['position'] = positions
        
        # Read velocity[] (float64 array)
        if decoder.pos + 4 <= len(data):
            vel_count = decoder.read_sequence_header()
            velocities = []
            for _ in range(vel_count):
                if decoder.pos + 8 <= len(data):
                    velocities.append(decoder.read_float64())
            result['velocity'] = velocities
        
        # Read effort[] (float64 array) - optional
        if decoder.pos + 4 <= len(data):
            effort_count = decoder.read_sequence_header()
            efforts = []
            for _ in range(effort_count):
                if decoder.pos + 8 <= len(data):
                    efforts.append(decoder.read_float64())
            result['effort'] = efforts
        
        return result
    
    except Exception as e:
        # On decode failure, return None
        return None


def decode_message(schema_name: str, data: bytes) -> Optional[Dict[str, Any]]:
    """
    Decode a message according to its schema name.

    Args:
        schema_name: Schema name (e.g. \"sensor_msgs/msg/JointState\").
        data: Raw message bytes.

    Returns:
        Decoded message dict, or None on failure.
    """
    # Normalize schema name
    schema_name_lower = schema_name.lower()
    
    if 'jointstate' in schema_name_lower:
        return decode_joint_state(data)
    
    # Additional message types can be added here
    # elif 'image' in schema_name_lower:
    #     return decode_image(data)
    
    return None


class MessageWrapper:
    """
    Message wrapper - provides a unified access interface.
    """
    
    def __init__(self, decoded: Optional[Dict[str, Any]]):
        self._data = decoded or {}
    
    @property
    def position(self) -> List[float]:
        """Get joint positions."""
        return self._data.get('position', [])
    
    @property
    def velocity(self) -> List[float]:
        """Get joint velocities."""
        return self._data.get('velocity', [])
    
    @property
    def effort(self) -> List[float]:
        """Get joint efforts."""
        return self._data.get('effort', [])
    
    @property
    def name(self) -> List[str]:
        """Get joint names."""
        return self._data.get('name', [])
    
    def is_valid(self) -> bool:
        """Return True if decoded message is valid."""
        return bool(self._data and self.position)


def decode_mcap_message(channel: Any, message: Any, schemas: Optional[Dict] = None) -> MessageWrapper:
    """
    Decode an MCAP message into a MessageWrapper.

    Args:
        channel: MCAP channel object.
        message: MCAP message object.
        schemas: Optional schema dictionary.

    Returns:
        MessageWrapper instance.
    """
    # Determine schema name
    schema_name = ''
    
    # Try to get schema from channel
    if hasattr(channel, 'schema') and channel.schema:
        schema_name = getattr(channel.schema, 'name', '')
    
    # If not found, try to get from schemas dict
    if not schema_name and schemas and hasattr(channel, 'schema_id'):
        schema = schemas.get(channel.schema_id)
        if schema:
            schema_name = getattr(schema, 'name', '')
    
    # Decode message
    decoded = decode_message(schema_name, message.data)
    
    return MessageWrapper(decoded)
