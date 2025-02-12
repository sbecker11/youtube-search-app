from dynamodb_utils.filter_utils import DynamoDbFilterUtils

if __name__ == "__main__":
    DynamoDbFilterUtils.test_select_dbItems_by_dbAttrs()

    DynamoDbFilterUtils.test_select_distinct_values_by_dbAttrs()

    DynamoDbFilterUtils.test_sort_dbItems_by_dbAttrs()
