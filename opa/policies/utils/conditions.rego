package utils.conditions

# true, если условия не заданы
conditions_match(conds, obj) := true if {
    not conds
}


conditions_match(conds, obj) := true if {
    conds
    not conds["$and"]
    not conds["$or"]
    # Простые условия по полям
    every k in object.keys(conds) {
        not startswith(k, "$")
        cond := conds[k]
        val := obj[k]
        operator_match(cond, val)
    }
}

conditions_match(conds, obj) := true if {
    # $and условия
    conds["$and"]
    and_conditions := conds["$and"]
    every and_cond in and_conditions {
        and_cond_matches(and_cond, obj)
    }
}

conditions_match(conds, obj) := true if {
    # $or условия
    conds["$or"]
    or_conditions := conds["$or"]
    some or_cond in or_conditions
    or_cond_matches(or_cond, obj)
}

# Проверка простого условия для $and
and_cond_matches(cond, obj) := true if {
    every k in object.keys(cond) {
        not startswith(k, "$")
        field_cond := cond[k]
        val := obj[k]
        operator_match(field_cond, val)
    }
}

# Проверка простого условия для $or
or_cond_matches(cond, obj) := true if {
    every k in object.keys(cond) {
        not startswith(k, "$")
        field_cond := cond[k]
        val := obj[k]
        operator_match(field_cond, val)
    }
}

# Проверка одного условия по полю
operator_match(cond, val) := true if {
    # $in
    cond["$in"]
    is_array(val)
    # Если val — список, хотя бы один элемент val должен быть в cond["$in"]
    some v in val
    some item in cond["$in"]
    v == item
}

operator_match(cond, val) := true if {
    # $in
    cond["$in"]
    not is_array(val)
    # Если val — не список, просто проверяем вхождение
    some item in cond["$in"]
    item == val
}

operator_match(cond, val) := true if {
    # $nin
    cond["$nin"]
    is_array(val)
    # Если val — список, ни один элемент val не должен входить в cond["$nin"]
    every v in val {
        not v in cond["$nin"]
    }
}

operator_match(cond, val) := true if {
    # $nin
    cond["$nin"]
    not is_array(val)
    # Если val — не список, просто проверяем отсутствие в cond["$nin"]
    not val in cond["$nin"]
}

operator_match(cond, val) := true if {
    # $gt
    cond["$gt"] < val
}

operator_match(cond, val) := true if {
    # $lt
    cond["$lt"] > val
}

operator_match(cond, val) := true if {
    # $gte
    cond["$gte"] <= val
}

operator_match(cond, val) := true if {
    # $lte
    cond["$lte"] >= val
}

operator_match(cond, val) := true if {
    # $ne
    cond["$ne"] != val
}

operator_match(cond, val) := true if {
    # $eq
    cond["$eq"] == val
}

operator_match(cond, val) := true if {
    # Точное совпадение (если cond — не объект с операторами)
    not is_object(cond)
    cond == val
}

# Вспомогательная функция: проверка, начинается ли строка с префикса
startswith(s, prefix) := true if {
    count(s) >= count(prefix)
    substring(s, 0, count(prefix)) == prefix
}

# Проверка, что значение — объект
is_object(x) := true if {
    object.keys(x)
}
