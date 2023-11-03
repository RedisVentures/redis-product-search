#!/usr/bin/env python3
import asyncio
import numpy as np
import os
import json
import typing as List

from productsearch import config

from redisvl.index import AsyncSearchIndex


def read_product_json_vectors() -> List:
    with open(config.DATA_LOCATION + "/product_vectors.json") as f:
        product_vectors = json.load(f)
    return product_vectors


async def write_products(index: AsyncSearchIndex, products: List[dict]):
    """
    Write product records to Redis.

    Args:
        index (AsyncSearchIndex): Redis search index.
        products (list): List of documents to store.
    """
    def preprocess(product: dict) -> dict:
        return {
                "product_id": product["product_id"],
                # add tag fields to vectors for hybrid search
                "gender": product["product_metadata"]["gender"],
                "category": product["product_metadata"]["master_category"],
                # add image and text vectors as blobs
                "img_vector": np.array(product["img_vector"], dtype=np.float32).tobytes(),
                "text_vector": np.array(product["text_vector"], dtype=np.float32).tobytes()
        }
    # TODO add an optional preprocessor callable to index.load()
    await index.load(
        data=[preprocess(product) for product in products],
        concurrency=config.WRITE_CONCURRENCY,
        key_field="product_id"
    )


async def load_data():
    index = AsyncSearchIndex.from_yaml(
        os.path.join("./schema", "products.yaml")
    )
    index.connect(config.REDIS_URL)

    # Check if index exists
    if await index.exists():
        print("Index already exists and products ")
    else:
        # create a search index
        await index.create(overwrite=True)
        print("Loading products from file")
        products = read_product_json_vectors()
        print("Loading products into Redis")
        await write_products(index, products)
        print("Products successfully loaded")


if __name__ == "__main__":
    asyncio.run(load_data())