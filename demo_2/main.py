import yaml
from gql import Client, gql
from gql.transport.aiohttp import AIOHTTPTransport
from pygnmi.client import gNMIclient


def get_config(path: str) -> dict:
    with open(path, mode="rt", encoding="utf-8") as f:
        r = yaml.load(f.read(), Loader=yaml.FullLoader)

    return r


def get_inventory(cfg: dict, site: str) -> dict:
    # Select your transport with a defined url endpoint
    transport = AIOHTTPTransport(
        url=f'{cfg["NB_URL"]}/graphql/',
        headers={"Authorization": f"Token {cfg['NB_TOKEN']}"},
    )

    # Create a GraphQL client using the defined transport
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Provide a GraphQL query
    query = gql(
        """
        query DevicePerSite($site: [String]) {
            device_list(site: $site)
            {
                name
                device_type {
                    model
                    manufacturer {
                        name
                    }
                }
                primary_ip4 {
                    address
                }
                interfaces {
                    name
                    type
                    ip_addresses {
                        address
                    }
                }
            }
        }
    """
    )

    # Execute the query on the transport
    result = client.execute(query, variable_values={"site": [site]})

    return result


def get_info_from_device(cfg: dict, dl: list) -> None:
    r = {}
    for device in dl:
        with gNMIclient(
            target=(device["primary_ip4"]["address"].split("/")[0], cfg["DEVICE_PORT"]),
            username=cfg["DEVICE_USERNAME"],
            password=cfg["DEVICE_PASSWORD"],
            insecure=True,
        ) as gconn:
            r[device["name"]] = gconn.get(path=["/interfaces/"])

    return r


if __name__ == "__main__":
    cfg = get_config("config.yaml")

    inventory = get_inventory(cfg=cfg, site="barcelona")

    device_data = get_info_from_device(cfg=cfg, dl=inventory["device_list"])

    print(device_data)
