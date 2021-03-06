// @flow
import * as React from 'react'
import styles from './styles.css'

export type CardRowProps = {|
  children: React.Node,
|}

export function CardRow(props: CardRowProps) {
  return <div className={styles.row}>{props.children}</div>
}
