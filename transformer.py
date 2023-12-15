# Transformer.

from typing import Callable, Optional, Sequence, Type

import numpy as np

import attention
import layer
import mlp


class LayerNormalization(layer.StatefulLayer):
    def __init__(self, epsilon: float = 1e-3, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._epsilon = epsilon

    def initialize(self, inputs: np.ndarray):
        col = inputs.shape[-1]
        self._gamma = self._initializer([col])
        self._beta = self._initializer([col])

    def forward(self, inputs: np.ndarray) -> np.ndarray:
        mean = np.mean(inputs, axis=-1, keepdims=True)
        var = np.var(inputs, axis=-1, keepdims=True)
        return self._gamma * (inputs -
                              mean) / np.sqrt(var + self._epsilon) + self._beta

    def backward(self, *args, **kwargs):
        raise NotImplementedError


class TransformerEncoder(layer.Layer):
    def __init__(self, num_heads: int, hidden_units: int, norm_first: bool,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._self_attention = attention.MultiHeadAttention(num_heads)
        self._dense1 = mlp.Dense(units=hidden_units)
        self._norm1 = LayerNormalization()
        self._norm2 = LayerNormalization()
        self._norm_first = norm_first

    def initialize(self, qkv: np.ndarray):
        features = qkv.shape[-1]
        self._dense2 = mlp.Linear(units=features)  # No activation

    def forward(self, qkv: np.ndarray) -> np.ndarray:
        # TODO: add mask support.
        # TODO: add dropout support.

        skip = qkv
        if self._norm_first:
            qkv = self._norm1(qkv)
        out = self._self_attention(qkv)
        out += skip
        if not self._norm_first:
            out = self._norm1(out)

        skip = out

        if self._norm_first:
            out = self._norm2(out)
        out = self._dense1(out)
        out = self._dense2(out)
        out += skip
        if not self._norm_first:
            out = self._norm2(out)

        return out

    def backward(self, *args, **kwargs):
        raise NotImplementedError


class TransformerDecoder(layer.Layer):
    def __init__(self, num_heads: int, hidden_units: int, norm_first: bool,
                 *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._self_attention = attention.MultiHeadAttention(num_heads)
        self._cross_attention = attention.MultiHeadAttention(num_heads)
        self._dense1 = mlp.Dense(units=hidden_units)
        self._norm1 = LayerNormalization()
        self._norm2 = LayerNormalization()
        self._norm3 = LayerNormalization()
        self._norm_first = norm_first

    def initialize(self, q: np.ndarray, kv: np.ndarray):
        features = q.shape[-1]
        self._dense2 = mlp.Linear(units=features)  # No activation

    def forward(self, q: np.ndarray, kv: np.ndarray) -> np.ndarray:
        # TODO: support cache

        skip = q
        if self._norm_first:
            q = self._norm1(q)
        out = self._self_attention(q)
        out += skip
        if not self._norm_first:
            out = self._norm1(out)

        skip = out

        if self._norm_first:
            out = self._norm2(out)
        out = self._cross_attention(out, kv)
        out += skip
        if not self._norm_first:
            out = self._norm2(out)

        skip = out

        if self._norm_first:
            out = self._norm3(out)
        out = self._dense1(out)
        out = self._dense2(out)
        out += skip
        if not self._norm_first:
            out = self._norm3(out)

        return out

    def backward(self, *args, **kwargs):
        raise NotImplementedError
