# Copyright (c) 2022, 2023 Humanitarian OpenStreetMap Team
#
# This file is part of osm_fieldwork.
#
#     Underpass is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Underpass is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with osm_fieldwork.  If not, see <https:#www.gnu.org/licenses/>.
#
"""Test functionalty of OdkCentral.py Entities methods."""

from datetime import datetime, timezone

import pytest


async def test_entity_modify(odk_entity_cleanup):
    """Test modifying an entity."""
    odk_id, dataset_name, entity_uuid, entity = odk_entity_cleanup
    async with entity:
        updated_entity = await entity.updateEntity(odk_id, dataset_name, entity_uuid, label="new label")
    assert updated_entity.get("currentVersion").get("label") == "new label"

    async with entity:
        updated_entity = await entity.updateEntity(
            odk_id, dataset_name, entity_uuid, data={"status": "complete", "project_id": "100"}
        )
    new_data = updated_entity.get("currentVersion").get("data", {})
    assert new_data.get("status") == "complete"
    assert new_data.get("project_id") == "100"


async def test_create_invalid_entities(odk_entity_cleanup):
    """Test uploading invalid data to an entity (HTTP 400)."""
    odk_id, dataset_name, entity_uuid, entity = odk_entity_cleanup
    async with entity:
        # NOTE entity must have a geometry data field
        with pytest.raises(ValueError):
            await entity.createEntity(odk_id, dataset_name, label="test", data={"status": 0})

        # NOTE data fields cannot be integer, this should 400 response
        invalid_data_type = await entity.createEntity(odk_id, dataset_name, label="test", data={"geometry": "", "status": 0})
        assert invalid_data_type == {}

        bulk_entities_one_invaid = await entity.createEntities(
            odk_id,
            dataset_name,
            {
                "test entity 2": {"osm_id": 55, "geometry": "test"},
                "test entity 3": {"osm_id": "66", "geometry": "test"},
            },
        )
        assert len(bulk_entities_one_invaid) == 1


async def test_bulk_create_entity_count(odk_entity_cleanup):
    """Test bulk creation of Entities."""
    odk_id, dataset_name, entity_uuid, entity = odk_entity_cleanup
    async with entity:
        created_entities = await entity.createEntities(
            odk_id,
            dataset_name,
            {
                "test entity 1": {"osm_id": "44", "geometry": "test"},
                "test entity 2": {"osm_id": "55", "geometry": "test"},
                "test entity 3": {"osm_id": "66", "geometry": "test"},
            },
        )
        entity_count = await entity.getEntityCount(odk_id, dataset_name)

    assert created_entities[0].get("currentVersion").get("data").get("geometry") == "test"
    # NOTE this may be cumulative from the session... either 4 or 5
    assert entity_count >= 4


async def test_get_entity_data(odk_entity_cleanup):
    """Test getting entity data, inluding via a OData filter."""
    odk_id, dataset_name, entity_uuid, entity = odk_entity_cleanup
    async with entity:
        new_entities = await entity.createEntities(
            odk_id,
            dataset_name,
            {
                "test entity 1": {"geometry": "test"},
                "test entity 2": {"geometry": "test"},
                "test entity 3": {"geometry": "test"},
                "test entity 4": {"geometry": "test"},
                "test entity 5": {"geometry": "test"},
                "test entity 6": {"geometry": "test"},
                "test entity 7": {"geometry": "test"},
                "test entity 8": {"geometry": "test"},
            },
        )

        all_entities = await entity.getEntityData(odk_id, dataset_name)
        # NOTE this may be cumulative from the session... either 9 or 12
        assert len(all_entities) >= 9

        entities_with_metadata = await entity.getEntityData(odk_id, dataset_name, include_metadata=True)
        assert len(entities_with_metadata.get("value")) >= 9
        assert entities_with_metadata.get("@odata.context").endswith("$metadata#Entities")

        # Paginate, 5 per page
        filtered_entities = await entity.getEntityData(odk_id, dataset_name, url_params="$top=5&$count=true")
        assert filtered_entities.get("@odata.count") >= 9
        assert "@odata.nextLink" in filtered_entities.keys()

        entity_uuids = [_entity.get("uuid") for _entity in new_entities]

        # Update all entities, so updatedAt is not 'None'
        for uuid in entity_uuids:
            await entity.updateEntity(odk_id, dataset_name, uuid, data={"status": "READY"})

        # Get current time NOTE time format = 2022-01-31T23:59:59.999Z
        time_now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # Update last 3 entities prior to filter
        entity_uuids = [_entity.get("uuid") for _entity in new_entities]
        for uuid in entity_uuids[5:]:
            await entity.updateEntity(odk_id, dataset_name, uuid, data={"status": "LOCKED_FOR_MAPPING"})

        filter_updated = await entity.getEntityData(
            odk_id,
            dataset_name,
            url_params=f"$filter=__system/updatedAt gt {time_now}",
        )
        assert len(filter_updated) == 3
        assert filter_updated[0].get("status") == "LOCKED_FOR_MAPPING"


async def test_get_entity_data_select_params(odk_entity_cleanup):
    """Test selecting specific param for an Entity."""
    odk_id, dataset_name, entity_uuid, entity = odk_entity_cleanup
    async with entity:
        entities_select_params = await entity.getEntityData(
            odk_id,
            dataset_name,
            url_params="$select=__id, __system/updatedAt, geometry",
        )

        assert entities_select_params, "No entities returned"
        first_entity = entities_select_params[0]
        assert "__id" in first_entity, "Missing '__id' key"
        assert "__system" in first_entity and "updatedAt" in first_entity["__system"], "Missing '__system/updatedAt' key"
        assert "geometry" in first_entity, "Missing 'geometry' key"


async def test_get_single_entity(odk_entity_cleanup):
    """Test getting specific Entity by UUID."""
    odk_id, dataset_name, entity_uuid, entity = odk_entity_cleanup
    async with entity:
        single_entity = await entity.getEntity(
            odk_id,
            dataset_name,
            entity_uuid,
        )

    assert single_entity.get("uuid") == entity_uuid
    entity_info = single_entity.get("currentVersion")
    # if ran in parallel, this is updated by test_entity_modify!
    assert (label := entity_info.get("label")) == "test entity" or label == "new label"
    assert entity_info.get("data", {}).get("osm_id") == "1"
